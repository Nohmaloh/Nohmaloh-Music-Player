# backend/config.py

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database settings
    DATABASE_URL = os.getenv(
        "DATABASE_URL", 
        "postgresql://user:password@localhost:5432/focus_music"
    )
    
    # Music folder settings
    MUSIC_FOLDER = os.getenv("MUSIC_FOLDER", "../music")
    
    # Supported audio formats
    SUPPORTED_FORMATS = {'.mp3', '.m4a', '.flac', '.wav'}
    
    # Server settings
    HOST = "127.0.0.1"
    PORT = 8000
    DEBUG = True

settings = Settings()

# Why these choices:
# - Configurable music folder location
# - Support multiple audio formats from the start