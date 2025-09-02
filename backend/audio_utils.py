# backend/audio_utils.py

import librosa
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class AudioTimeCalculator:
    """
    Utilities for audio time synchronization between original and processed versions
    
    Why a separate class?
    - Complex time calculations need to be precise
    - Reusable across different processing scenarios  
    - Easier to test mathematical logic
    - Future: Could add more sophisticated sync methods
    """
    
    @staticmethod
    def calculate_sync_position(original_position: float, 
                              original_bpm: float,
                              processed_bpm: float) -> float:
        """
        Calculate equivalent position in processed audio
        
        This is critical for seamless transitions!
        
        Args:
            original_position: Current position in original track (seconds)
            original_bpm: BPM of original track
            processed_bpm: BPM of processed track
            
        Returns:
            Equivalent position in processed track (seconds)
            
        Example:
            Original at 2:30 (150s) @ 120 BPM
            Processed @ 80 BPM (slower)
            Tempo ratio = 80/120 = 0.667
            Processed position = 150 * 0.667 = 100s
        """
        if original_bpm <= 0 or processed_bpm <= 0:
            logger.warning("Invalid BPM values, using 1:1 ratio")
            return original_position
        
        tempo_ratio = processed_bpm / original_bpm
        processed_position = original_position * tempo_ratio
        
        logger.debug(f"Sync calculation: {original_position}s @ {original_bpm} BPM "
                    f"→ {processed_position}s @ {processed_bpm} BPM")
        
        return processed_position
    
    @staticmethod
    def calculate_tempo_ratio(original_bpm: float, processed_bpm: float) -> float:
        """
        Calculate tempo ratio between original and processed audio
        
        Returns:
            Ratio (e.g., 0.8 = processed is 80% speed of original)
        """
        if original_bpm <= 0:
            return 1.0
        return processed_bpm / original_bpm
    
    @staticmethod  
    def estimate_processing_time(duration_seconds: float, 
                               focus_intensity: int) -> float:
        """
        Estimate how long focus processing will take
        
        Why estimate? Users need to know how long to wait
        
        Based on:
        - Spleeter separation: ~0.5x real time
        - Audio effects: ~0.1x real time  
        - File I/O: ~0.1x real time
        - Higher intensity = more processing
        """
        base_time = duration_seconds * 0.7  # Base processing overhead
        intensity_factor = 1.0 + (focus_intensity / 100.0) * 0.3  # Up to 30% more for high intensity
        
        estimated_time = base_time * intensity_factor
        
        # Add minimum time for model loading/initialization
        estimated_time = max(estimated_time, 10.0)
        
        logger.debug(f"Estimated processing time: {estimated_time:.1f}s for {duration_seconds:.1f}s audio")
        return estimated_time

class AudioAnalyzer:
    """
    Advanced audio analysis utilities
    
    Separated from FocusProcessor for modularity
    """
    
    @staticmethod
    def analyze_audio_file(file_path: str) -> dict:
        """
        Comprehensive audio file analysis
        
        Returns metadata that's useful for processing decisions
        """
        try:
            # Load audio for analysis
            y, sr = librosa.load(file_path, sr=None, mono=False)
            
            # Handle stereo/mono
            if len(y.shape) == 2:
                y_mono = librosa.to_mono(y)
                is_stereo = True
            else:
                y_mono = y
                is_stereo = False
            
            # Basic properties
            duration = len(y_mono) / sr
            
            # Advanced analysis
            tempo = librosa.feature.tempo(y=y_mono, sr=sr)[0]
            
            # Spectral analysis
            spectral_centroids = librosa.feature.spectral_centroid(y=y_mono, sr=sr)[0]
            avg_spectral_centroid = np.mean(spectral_centroids)
            
            # Dynamic range analysis
            rms = librosa.feature.rms(y=y_mono)[0]
            dynamic_range = np.max(rms) - np.min(rms)
            
            # Key signature detection (basic)
            chroma = librosa.feature.chroma_stft(y=y_mono, sr=sr)
            key_profile = np.mean(chroma, axis=1)
            estimated_key = np.argmax(key_profile)
            key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            
            analysis = {
                'duration': duration,
                'sample_rate': sr,
                'is_stereo': is_stereo,
                'tempo': float(tempo),
                'spectral_centroid': float(avg_spectral_centroid),
                'dynamic_range': float(dynamic_range),
                'estimated_key': key_names[estimated_key],
                'key_confidence': float(key_profile[estimated_key]),
                'processing_complexity': AudioAnalyzer._estimate_complexity(
                    tempo, dynamic_range, avg_spectral_centroid
                )
            }
            
            logger.info(f"Audio analysis complete: {analysis}")
            return analysis
            
        except Exception as e:
            logger.error(f"Audio analysis failed: {e}")
            return {
                'error': str(e),
                'duration': 0,
                'tempo': 120.0  # Fallback BPM
            }
    
    @staticmethod
    def _estimate_complexity(tempo: float, dynamic_range: float, 
                           spectral_centroid: float) -> str:
        """
        Estimate processing complexity based on audio characteristics
        
        Why? Different songs need different processing approaches
        """
        complexity_score = 0
        
        # Fast tempo = more complex
        if tempo > 140:
            complexity_score += 2
        elif tempo > 100:
            complexity_score += 1
        
        # High dynamic range = more complex
        if dynamic_range > 0.5:
            complexity_score += 2
        elif dynamic_range > 0.3:
            complexity_score += 1
        
        # High spectral content = more complex
        if spectral_centroid > 3000:
            complexity_score += 2
        elif spectral_centroid > 2000:
            complexity_score += 1
        
        if complexity_score >= 5:
            return "high"
        elif complexity_score >= 3:
            return "medium"
        else:
            return "low"

class AudioValidator:
    """
    Validation utilities for audio processing
    """
    
    @staticmethod
    def validate_audio_file(file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if audio file can be processed
        
        Returns:
            (is_valid, error_message)
        """
        try:
            # Check file exists
            import os
            if not os.path.exists(file_path):
                return False, "File does not exist"
            
            # Check file size (prevent extremely large files)
            file_size = os.path.getsize(file_path)
            max_size = 100 * 1024 * 1024  # 100MB limit
            if file_size > max_size:
                return False, f"File too large: {file_size / 1024 / 1024:.1f}MB (max 100MB)"
            
            # Try to load audio
            y, sr = librosa.load(file_path, sr=None, duration=1.0)  # Load just 1 second for validation
            
            # Check duration
            if len(y) == 0:
                return False, "Audio file appears to be empty"
            
            # Check if it's too short (minimum 10 seconds for meaningful processing)
            full_y, _ = librosa.load(file_path, sr=None)
            duration = len(full_y) / sr
            if duration < 10:
                return False, f"Audio too short: {duration:.1f}s (minimum 10s)"
            
            # Check if it's too long (prevent excessive processing time)
            max_duration = 600  # 10 minutes
            if duration > max_duration:
                return False, f"Audio too long: {duration/60:.1f}min (maximum {max_duration/60:.1f}min)"
            
            return True, None
            
        except Exception as e:
            return False, f"Invalid audio file: {str(e)}"
    
    @staticmethod
    def validate_focus_parameters(focus_intensity: int, target_bpm: int) -> Tuple[bool, Optional[str]]:
        """
        Validate focus processing parameters
        
        Args:
            focus_intensity: 0-100
            target_bpm: 0 (auto) or 30-200
            
        Returns:
            (is_valid, error_message)
        """
        # Validate focus intensity
        if not 0 <= focus_intensity <= 100:
            return False, f"Focus intensity must be 0-100, got {focus_intensity}"
        
        # Validate target BPM
        if target_bpm != 0 and not (30 <= target_bpm <= 200):
            return False, f"Target BPM must be 0 (auto) or 30-200, got {target_bpm}"
        
        return True, None

# Convenience functions for API use
def sync_audio_position(original_pos: float, original_bpm: float, 
                       processed_bpm: float) -> float:
    """Convenience wrapper for position synchronization"""
    return AudioTimeCalculator.calculate_sync_position(
        original_pos, original_bpm, processed_bpm
    )

def estimate_processing_duration(audio_duration: float, intensity: int) -> float:
    """Convenience wrapper for processing time estimation"""
    return AudioTimeCalculator.estimate_processing_time(audio_duration, intensity)

def validate_processing_request(file_path: str, intensity: int, 
                              target_bpm: int) -> Tuple[bool, Optional[str]]:
    """
    Complete validation for a processing request
    
    Returns:
        (is_valid, error_message)
    """
    # Validate file
    file_valid, file_error = AudioValidator.validate_audio_file(file_path)
    if not file_valid:
        return False, file_error
    
    # Validate parameters
    params_valid, params_error = AudioValidator.validate_focus_parameters(intensity, target_bpm)
    if not params_valid:
        return False, params_error
    
    return True, None

if __name__ == "__main__":
    # Test the utilities
    import sys
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        
        print("Validating file...")
        is_valid, error = AudioValidator.validate_audio_file(test_file)
        print(f"Valid: {is_valid}, Error: {error}")
        
        if is_valid:
            print("\nAnalyzing audio...")
            analysis = AudioAnalyzer.analyze_audio_file(test_file)
            print(f"Analysis: {analysis}")
            
            print("\nTesting sync calculation...")
            sync_pos = sync_audio_position(150.0, 120.0, 80.0)
            print(f"Sync position: 150s @ 120 BPM → {sync_pos}s @ 80 BPM")
    else:
        print("Usage: python audio_utils.py <audio_file>")

# Why this modular design:
# 1. Single responsibility - each class handles one aspect
# 2. Testable - can unit test each utility independently
# 3. Reusable - functions can be used by API, CLI tools, etc.
# 4. Validation - prevents bad inputs from causing processing failures  
# 5. Analysis - helps optimize processing for different audio types
# 6. Time sync - critical for seamless audio transitions