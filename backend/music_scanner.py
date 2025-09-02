# backend/music_scanner.py

import os
from pathlib import Path
from typing import Optional, Dict, Any
from mutagen import File as MutagenFile
from mutagen.id3 import ID3NoHeaderError
from sqlalchemy.orm import Session
from models import Song
from database import SessionLocal, engine
from config import settings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MusicScanner:
    """
    Scans local music folder and extracts metadata
    
    Why mutagen? 
    - Supports all major audio formats (MP3, M4A, FLAC, etc.)
    - Extracts comprehensive metadata
    - Handles corrupted files gracefully
    """
    
    def __init__(self, music_folder: str = settings.MUSIC_FOLDER):
        self.music_folder = Path(music_folder)
        
    def extract_metadata(self, filepath: Path) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from audio file using mutagen
        Returns None if file can't be read
        """
        try:
            audio_file = MutagenFile(filepath)
            if audio_file is None:
                logger.warning(f"Could not read audio file: {filepath}")
                return None
            
            # Get basic file info
            file_info = {
                'filename': filepath.name,
                'filepath': str(filepath.relative_to(self.music_folder)),
                'file_size': filepath.stat().st_size,
                'file_format': filepath.suffix.lower()[1:],  # Remove the dot
            }
            
            # Extract audio metadata
            # Why this approach: Handle missing tags gracefully
            metadata = {
                'title': self._get_tag(audio_file, ['TIT2', 'TITLE', '\xa9nam']),
                'artist': self._get_tag(audio_file, ['TPE1', 'ARTIST', '\xa9ART']),
                'album': self._get_tag(audio_file, ['TALB', 'ALBUM', '\xa9alb']),
                'genre': self._get_tag(audio_file, ['TCON', 'GENRE', '\xa9gen']),
                'year': self._get_year(audio_file),
                'track_number': self._get_track_number(audio_file),
            }
            
            # Audio properties
            if hasattr(audio_file, 'info'):
                metadata.update({
                    'duration': getattr(audio_file.info, 'length', None),
                    'bitrate': getattr(audio_file.info, 'bitrate', None),
                    'sample_rate': getattr(audio_file.info, 'sample_rate', None),
                })
            
            # Fallback: use filename as title if no metadata
            if not metadata['title']:
                metadata['title'] = filepath.stem  # Filename without extension
                
            if not metadata['artist']:
                metadata['artist'] = 'Unknown Artist'
            
            return {**file_info, **metadata}
            
        except Exception as e:
            logger.error(f"Error processing {filepath}: {e}")
            return None
    
    def _get_tag(self, audio_file, tag_names: list) -> Optional[str]:
        """Try multiple tag name variations to get a value"""
        for tag_name in tag_names:
            if tag_name in audio_file:
                value = audio_file[tag_name]
                if isinstance(value, list) and value:
                    return str(value[0])
                elif value:
                    return str(value)
        return None
    
    def _get_year(self, audio_file) -> Optional[int]:
        """Extract year from various date formats"""
        year_tags = ['TDRC', 'TYER', 'DATE', '\xa9day']
        for tag in year_tags:
            if tag in audio_file:
                date_value = str(audio_file[tag][0] if isinstance(audio_file[tag], list) else audio_file[tag])
                # Extract first 4 digits (year)
                year_match = ''.join(filter(str.isdigit, date_value))[:4]
                if len(year_match) == 4:
                    return int(year_match)
        return None
    
    def _get_track_number(self, audio_file) -> Optional[int]:
        """Extract track number"""
        track_tags = ['TRCK', 'TRACKNUMBER', 'trkn']
        for tag in track_tags:
            if tag in audio_file:
                track_value = str(audio_file[tag][0] if isinstance(audio_file[tag], list) else audio_file[tag])
                # Handle "1/12" format - take first number
                track_num = track_value.split('/')[0]
                try:
                    return int(track_num)
                except ValueError:
                    continue
        return None
    
    def scan_folder(self, db: Session) -> int:
        """
        Scan music folder and add new songs to database
        Returns number of songs added
        """
        if not self.music_folder.exists():
            logger.error(f"Music folder not found: {self.music_folder}")
            return 0
        
        logger.info(f"Scanning music folder: {self.music_folder}")
        
        # Get all existing filepaths from database
        existing_paths = {song.filepath for song in db.query(Song.filepath).all()}
        
        songs_added = 0
        songs_processed = 0
        
        # Recursively scan all audio files
        for audio_file in self.music_folder.rglob('*'):
            if audio_file.suffix.lower() in settings.SUPPORTED_FORMATS:
                songs_processed += 1
                
                # Skip if already in database
                relative_path = str(audio_file.relative_to(self.music_folder))
                if relative_path in existing_paths:
                    continue
                
                # Extract metadata and add to database
                metadata = self.extract_metadata(audio_file)
                if metadata:
                    song = Song(**metadata)
                    db.add(song)
                    songs_added += 1
                    logger.info(f"Added: {metadata['title']} by {metadata['artist']}")
        
        # Commit all changes
        db.commit()
        
        logger.info(f"Scan complete: {songs_processed} files processed, {songs_added} new songs added")
        return songs_added

def scan_music_library():
    """Convenience function to scan music library"""
    scanner = MusicScanner()
    db = SessionLocal()
    try:
        return scanner.scan_folder(db)
    finally:
        db.close()

if __name__ == "__main__":
    # Run scanner when executing this file directly
    songs_added = scan_music_library()
    print(f"Music library scan complete. Added {songs_added} new songs.")

# Why this design:
# 1. Handles missing metadata gracefully - uses filename as fallback
# 2. Incremental scanning - only processes new files
# 3. Supports multiple audio formats out of the box
# 4. Proper error handling - one bad file won't crash everything
# 5. Logging for debugging and monitoring