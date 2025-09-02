from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pathlib import Path
from typing import List, Optional
from contextlib import asynccontextmanager
import uvicorn
import logging

from database import get_db, create_tables
from models import Song
from music_scanner import scan_music_library
from config import settings
from focus_api import focus_router
from processing_queue import initialize_queue, shutdown_queue

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for FastAPI application
    
    Why this pattern?
    - Modern FastAPI approach (replaces deprecated @app.on_event)
    - Context manager ensures proper cleanup
    - Handles both startup and shutdown in one place
    - Better error handling and resource management
    """
    # Startup events
    logger.info("Starting Focus Music Player API...")
    
    try:
        # Create database tables
        create_tables()
        logger.info("Database tables created/verified")
        
        # Initialize processing queue
        await initialize_queue()
        logger.info("Processing queue initialized")
        
        logger.info("Focus Music Player API started successfully!")
        logger.info(f"API Documentation: http://{settings.HOST}:{settings.PORT}/docs")
        logger.info(f"Alternative docs: http://{settings.HOST}:{settings.PORT}/redoc")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    # Yield control to the application
    # Everything before yield runs on startup
    # Everything after yield runs on shutdown
    yield
    
    # Shutdown events
    logger.info("Shutting down Focus Music Player API...")
    
    try:
        # Shutdown processing queue
        await shutdown_queue()
        logger.info("Processing queue shut down")
        
        logger.info("Focus Music Player API shut down successfully!")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
        # Don't raise here - we're shutting down anyway

# Create FastAPI app with lifespan handler
app = FastAPI(
    title="Focus Music Player API",
    description="Backend API for the Focus Music Player with Focus Mode Processing",
    version="2.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # Alternative docs
    lifespan=lifespan  # Modern lifespan event handler
)

# CORS middleware - allows React frontend to call our API
# Why CORS: Browser security prevents cross-origin requests by default
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React development server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include focus processing router
app.include_router(focus_router)

# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Focus Music Player API is running!"}

@app.get("/songs", response_model=List[dict])
async def get_songs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get songs from the library with optional search and pagination
    
    Why pagination: Large music libraries need efficient loading
    Why search: Users need to find specific songs quickly
    """
    query = db.query(Song).filter(Song.is_available == True)
    
    # Add search filter if provided
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Song.title.ilike(search_filter)) |
            (Song.artist.ilike(search_filter)) |
            (Song.album.ilike(search_filter))
        )
    
    # Apply pagination
    songs = query.offset(offset).limit(limit).all()
    
    # Convert to dictionaries for JSON response
    return [
        {
            "id": song.id,
            "title": song.title,
            "artist": song.artist,
            "album": song.album,
            "duration": song.duration,
            "filepath": song.filepath,
            "file_format": song.file_format,
            "year": song.year,
            "genre": song.genre,
        }
        for song in songs
    ]

@app.get("/songs/{song_id}")
async def get_song(song_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific song"""
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    
    return {
        "id": song.id,
        "title": song.title,
        "artist": song.artist,
        "album": song.album,
        "duration": song.duration,
        "filepath": song.filepath,
        "file_format": song.file_format,
        "bitrate": song.bitrate,
        "sample_rate": song.sample_rate,
        "year": song.year,
        "genre": song.genre,
        "bpm": song.bpm,
    }

@app.get("/audio/{song_id}")
async def stream_audio(song_id: int, db: Session = Depends(get_db)):
    """
    Stream audio file to frontend
    
    Why streaming: Allows playback to start immediately without downloading entire file
    """
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    
    # Construct full file path
    audio_path = Path(settings.MUSIC_FOLDER) / song.filepath
    
    if not audio_path.exists():
        # Mark song as unavailable
        song.is_available = False
        db.commit()
        raise HTTPException(status_code=404, detail="Audio file not found on disk")
    
    # Return file with proper headers for audio streaming
    return FileResponse(
        audio_path,
        media_type=f"audio/{song.file_format}",
        headers={
            "Accept-Ranges": "bytes",  # Enable seeking in audio player
            "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
        }
    )

@app.post("/scan")
async def scan_music():
    """
    Manually trigger music library scan
    Useful for adding new songs without restarting server
    """
    try:
        songs_added = scan_music_library()
        return {
            "message": f"Scan completed successfully",
            "songs_added": songs_added
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

@app.get("/stats")
async def get_library_stats(db: Session = Depends(get_db)):
    """Get basic statistics about the music library"""
    total_songs = db.query(Song).count()
    available_songs = db.query(Song).filter(Song.is_available == True).count()
    
    # Get some interesting stats
    artists = db.query(Song.artist).distinct().count()
    albums = db.query(Song.album).distinct().count()
    
    return {
        "total_songs": total_songs,
        "available_songs": available_songs,
        "unavailable_songs": total_songs - available_songs,
        "unique_artists": artists,
        "unique_albums": albums,
    }

# Development helper endpoints

@app.post("/dev/rescan")
async def force_rescan():
    """Development only: Force complete rescan of music library"""
    if not settings.DEBUG:
        raise HTTPException(status_code=403, detail="Only available in debug mode")
    
    # This would clear database and rescan everything
    # Implementation depends on your needs
    return {"message": "Force rescan not implemented yet"}

if __name__ == "__main__":
    # Run with: python app.py
    print(f"Starting server on {settings.HOST}:{settings.PORT}")
    print(f"Music folder: {settings.MUSIC_FOLDER}")
    print(f"API docs available at: http://{settings.HOST}:{settings.PORT}/docs")
    
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,  # Auto-reload on file changes during development
    )

# Why this API design:
# 1. RESTful endpoints - predictable URL structure
# 2. Proper HTTP status codes - 404 for not found, 500 for server errors
# 3. Pagination - handle large libraries efficiently
# 4. Search functionality - essential for music libraries
# 5. Audio streaming - enables instant playback
# 6. Error handling - graceful degradation when files are missing
# 7. Development helpers - make testing easier