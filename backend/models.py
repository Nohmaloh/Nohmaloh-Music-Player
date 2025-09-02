# backend/models.py

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class Song(Base):
    """
    Core song model - stores metadata about each track
    
    Why these fields:
    - id: Primary key for database relationships
    - filepath: Relative path to music file (portable between systems)
    - title/artist/album: Basic metadata for UI display
    - duration: For progress bars and time display
    - bpm: Will be useful for focus mode processing
    - file_size: For storage management
    - created_at: Track when songs were added
    - is_available: Handle missing files gracefully
    """
    __tablename__ = "songs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # File information
    filename = Column(String, nullable=False, index=True)  # Original filename
    filepath = Column(String, nullable=False, unique=True)  # Relative path from music folder
    file_size = Column(Integer)  # Size in bytes
    file_format = Column(String)  # mp3, m4a, etc.
    
    # Metadata from audio file
    title = Column(String, index=True)
    artist = Column(String, index=True)
    album = Column(String)
    genre = Column(String)
    year = Column(Integer)
    track_number = Column(Integer)
    
    # Audio properties
    duration = Column(Float)  # Duration in seconds
    bitrate = Column(Integer)  # Audio quality
    sample_rate = Column(Integer)
    bpm = Column(Float, nullable=True)  # Will be detected later for focus mode
    
    # System fields
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_available = Column(Boolean, default=True)  # False if file is missing
    
    def __repr__(self):
        return f"<Song(title='{self.title}', artist='{self.artist}')>"

class ProcessedVersion(Base):
    """
    Stores focus-mode processed versions of songs
    """
    __tablename__ = "processed_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    song_id = Column(Integer, index=True)  # References songs.id (Foreign key can be added later)
    
    # Processing parameters
    focus_intensity = Column(Integer, nullable=False)  # 0-100
    target_bpm = Column(Float, nullable=True)  # User-specified BPM or NULL for auto
    
    # Processed file info
    processed_filepath = Column(String, nullable=False)  # Path to processed MP3
    processed_duration = Column(Float)  # Duration in seconds
    actual_bpm = Column(Float)  # Actual BPM after processing
    
    # System fields
    created_at = Column(DateTime, default=func.now())
    file_size = Column(Integer)  # File size in bytes
    
    def __repr__(self):
        return f"<ProcessedVersion(song_id={self.song_id}, intensity={self.focus_intensity}%)>"

# Why this design:
# 1. Separate table for processed versions - allows multiple focus levels per song
# 2. Nullable fields - handle incomplete metadata gracefully  
# 3. Index on commonly searched fields (title, artist, filepath)
# 4. Timestamps for debugging and analytics
# 5. is_available flag - handle missing files without breaking the app