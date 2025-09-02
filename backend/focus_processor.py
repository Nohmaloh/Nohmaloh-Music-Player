import librosa
import numpy as np
import soundfile as sf
import tempfile
import os
from spleeter.separator import Separator
from pydub import AudioSegment
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import logging
from scipy import signal

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FocusProcessor:
    """
    Core audio processing for focus mode transformation
    
    Extracted from your Gradio app and optimized for API usage
    
    Why a class?
    - Encapsulates Spleeter model (expensive to load repeatedly)
    - Maintains processing state
    - Easier to test and mock
    - Can add caching later
    """
    
    def __init__(self):
        """Initialize Spleeter model (this is expensive, so do it once)"""
        logger.info("Loading Spleeter model...")
        try:
            self.separator = Separator('spleeter:2stems')
            logger.info("Spleeter loaded successfully!")
        except Exception as e:
            logger.error(f"Failed to load Spleeter: {e}")
            raise
    
    def numpy_to_mp3(self, audio_array: np.ndarray, sample_rate: int, 
                     output_file: str, bitrate: str = "320k") -> str:
        """
        Convert numpy array to MP3 using pydub
        
        Why this function?
        - Handles stereo/mono conversion automatically
        - Consistent MP3 encoding
        - Better compression than raw audio
        """
        # Ensure audio is in the right format
        if len(audio_array.shape) == 2:
            # Stereo: transpose to get (samples, channels)
            audio_data = audio_array.T
        else:
            # Mono: reshape to (samples, 1)
            audio_data = audio_array.reshape(-1, 1)
        
        # Convert to 16-bit integers (standard for audio)
        audio_data = (audio_data * 32767).astype(np.int16)
        
        # Create AudioSegment
        if audio_data.shape[1] == 1:
            # Mono
            audio_segment = AudioSegment(
                audio_data.tobytes(),
                frame_rate=sample_rate,
                sample_width=2,  # 16-bit = 2 bytes
                channels=1
            )
        else:
            # Stereo
            audio_segment = AudioSegment(
                audio_data.tobytes(),
                frame_rate=sample_rate,
                sample_width=2,  # 16-bit = 2 bytes  
                channels=2
            )
        
        # Export as MP3
        audio_segment.export(output_file, format="mp3", bitrate=bitrate)
        return output_file
    
    def detect_bpm(self, audio: np.ndarray, sample_rate: int) -> float:
        """
        Detect BPM of audio using librosa
        
        Why separate function?
        - Can be used independently for analysis
        - Different algorithms might be used later
        - Easier to test BPM detection specifically
        """
        try:
            # Use first channel for BPM detection if stereo
            audio_mono = audio[0] if len(audio.shape) == 2 else audio
            tempo = librosa.feature.tempo(y=audio_mono, sr=sample_rate)[0]
            return float(tempo)
        except Exception as e:
            logger.warning(f"BPM detection failed: {e}, using default 120 BPM")
            return 120.0  # Fallback BPM
    
    def calculate_tempo_ratio(self, original_bpm: float, target_bpm: float, 
                            focus_intensity: float) -> float:
        """
        Calculate tempo adjustment ratio
        
        Args:
            original_bpm: Detected BPM of original song
            target_bpm: User-specified target BPM (0 = auto)
            focus_intensity: 0-100 intensity level
            
        Returns:
            Ratio to apply to audio (e.g., 0.8 = slow down by 20%)
        """
        intensity = focus_intensity / 100.0
        
        if target_bpm > 0:
            # User specified target BPM
            return target_bpm / original_bpm
        else:
            # Auto-calculate based on intensity (from your original logic)
            target_tempo = max(50, original_bpm * (1 - intensity * 0.5))
            return target_tempo / original_bpm
    
    def apply_focus_effects(self, vocals: np.ndarray, accompaniment: np.ndarray,
                          sample_rate: int, focus_intensity: float, 
                          tempo_ratio: float) -> np.ndarray:
        """
        Apply focus-friendly effects to separated audio stems
        
        This is the core transformation logic from your Gradio app
        
        Why separate function?
        - Can test effects independently of separation
        - Easier to adjust effect parameters
        - Could add more effect types later
        """
        intensity = focus_intensity / 100.0
        
        # Process vocals with tempo adjustment
        logger.info("Processing vocals...")
        vocals_processed = librosa.effects.time_stretch(vocals, rate=tempo_ratio)
        
        # Apply filtering to vocals if intensity is moderate+
        if intensity > 0.3:
            logger.info("Applying vocal filtering...")
            # Gentle low-pass filter to soften harsh frequencies
            nyquist = sample_rate / 2
            cutoff = 3000 * (1 - intensity * 0.5)  # Lower cutoff = more filtering
            b, a = signal.butter(4, cutoff / nyquist, btype='low')
            vocals_processed = signal.filtfilt(b, a, vocals_processed)
        
        # Reduce vocal volume based on intensity
        vocal_volume = 1.0 - (intensity * 0.7)  # Max 70% reduction
        vocals_processed = vocals_processed * vocal_volume
        
        # Process accompaniment
        logger.info("Processing accompaniment...")
        accompaniment_processed = librosa.effects.time_stretch(accompaniment, rate=tempo_ratio)
        
        # Apply gentle processing to accompaniment
        if intensity > 0.2:
            logger.info("Applying accompaniment filtering...")
            cutoff_acc = 5000 * (1 - intensity * 0.3)
            nyquist = sample_rate / 2
            b, a = signal.butter(3, cutoff_acc / nyquist, btype='low')
            accompaniment_processed = signal.filtfilt(b, a, accompaniment_processed)
        
        # Mix the processed stems
        logger.info("Mixing final audio...")
        final_mix = vocals_processed + accompaniment_processed
        
        # Normalize to prevent clipping
        max_val = np.max(np.abs(final_mix))
        if max_val > 0.95:
            final_mix = final_mix * (0.95 / max_val)
        
        return final_mix
    
    def process_audio_for_focus(self, input_file_path: str, focus_intensity: int,
                              target_bpm: int = 0) -> Dict[str, Any]:
        """
        Main processing function - transforms audio for focus mode
        
        This is adapted from your Gradio app's process_audio_for_focus function
        
        Args:
            input_file_path: Path to original audio file
            focus_intensity: 0-100 intensity level
            target_bpm: Target BPM (0 = auto)
            
        Returns:
            Dictionary with processing results and file paths
        """
        try:
            logger.info(f"Starting focus processing: {input_file_path}")
            logger.info(f"Parameters: intensity={focus_intensity}%, target_bpm={target_bpm}")
            
            # Load audio
            waveform, sample_rate = librosa.load(input_file_path, sr=44100, mono=False)
            
            # Handle mono files
            if len(waveform.shape) == 1:
                waveform = np.stack([waveform, waveform])
            
            # Get song duration for calculations
            duration_seconds = waveform.shape[1] / sample_rate
            logger.info(f"Original duration: {duration_seconds:.1f}s")
            
            # Separate vocals and accompaniment using Spleeter
            logger.info("Separating stems with Spleeter...")
            prediction = self.separator.separate(waveform.T)
            
            vocals = prediction['vocals'].T
            accompaniment = prediction['accompaniment'].T
            
            # Detect original BPM
            logger.info("Detecting BPM...")
            original_bpm = self.detect_bpm(vocals, sample_rate)
            logger.info(f"Detected BPM: {original_bpm:.1f}")
            
            # Calculate tempo adjustment
            tempo_ratio = self.calculate_tempo_ratio(original_bpm, target_bpm, focus_intensity)
            new_bpm = original_bpm * tempo_ratio
            new_duration = duration_seconds / tempo_ratio
            
            logger.info(f"Tempo ratio: {tempo_ratio:.3f}, New BPM: {new_bpm:.1f}")
            
            # Apply focus effects
            final_mix = self.apply_focus_effects(
                vocals, accompaniment, sample_rate, focus_intensity, tempo_ratio
            )
            
            # Create temporary output file
            output_file = tempfile.NamedTemporaryFile(
                delete=False, 
                suffix='_focus.mp3',
                prefix='focus_'
            )
            
            # Convert to MP3
            logger.info("Converting to MP3...")
            self.numpy_to_mp3(final_mix, sample_rate, output_file.name, bitrate="320k")
            
            # Calculate processing results
            intensity_ratio = focus_intensity / 100.0
            vocal_reduction = int(intensity_ratio * 70)
            
            result = {
                'success': True,
                'processed_file_path': output_file.name,
                'original_duration': duration_seconds,
                'processed_duration': new_duration,
                'original_bpm': original_bpm,
                'processed_bpm': new_bpm,
                'tempo_ratio': tempo_ratio,
                'focus_intensity': focus_intensity,
                'vocal_reduction_percent': vocal_reduction,
                'processing_info': {
                    'stems_separated': True,
                    'effects_applied': intensity_ratio > 0.3,
                    'vocal_filtering': intensity_ratio > 0.3,
                    'accompaniment_filtering': intensity_ratio > 0.2,
                }
            }
            
            logger.info("Focus processing completed successfully!")
            return result
            
        except Exception as e:
            logger.error(f"Focus processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }

# Global processor instance
# Why global? Spleeter model loading is expensive (5-10 seconds)
# Loading once and reusing is much more efficient
_processor_instance = None

def get_focus_processor() -> FocusProcessor:
    """
    Get or create global FocusProcessor instance
    
    Singleton pattern ensures Spleeter model is loaded only once
    """
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = FocusProcessor()
    return _processor_instance

# Convenience function for direct use
def process_song_for_focus(input_file: str, focus_intensity: int, 
                          target_bpm: int = 0) -> Dict[str, Any]:
    """
    Convenience function to process a song for focus mode
    
    This is the main entry point for the API
    """
    processor = get_focus_processor()
    return processor.process_audio_for_focus(input_file, focus_intensity, target_bpm)

if __name__ == "__main__":
    # Test the processor with a sample file
    import sys
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        result = process_song_for_focus(test_file, 50)
        print("Processing result:", result)
    else:
        print("Usage: python focus_processor.py <audio_file>")

# Why this architecture:
# 1. Separation of concerns - each function has one responsibility
# 2. Singleton pattern - expensive model loading done once
# 3. Comprehensive error handling - graceful degradation
# 4. Logging - essential for debugging audio processing
# 5. Testable - each function can be tested independently
# 6. Reusable - can be imported and used by API or other tools