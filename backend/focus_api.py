# backend/focus_api.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from pathlib import Path
import logging

from database import get_db
from models import Song, ProcessedVersion
from config import settings
from audio_utils import validate_processing_request, estimate_processing_duration, AudioAnalyzer
from processing_queue import (
    submit_processing_job, 
    get_job_info, 
    cancel_processing_job,
    get_processing_queue
)

logger = logging.getLogger(__name__)

# Create router for focus-related endpoints
# Why separate router? Keeps focus endpoints organized and modular
focus_router = APIRouter(prefix="/focus", tags=["Focus Processing"])

# Pydantic models for request/response validation
# Why Pydantic? Automatic validation, documentation, and type checking

class FocusProcessingRequest(BaseModel):
    """Request model for focus processing"""
    focus_intensity: int = Field(..., ge=0, le=100, description="Focus intensity (0-100%)")
    target_bpm: int = Field(0, ge=0, le=200, description="Target BPM (0 = auto)")
    
    class Config:
        schema_extra = {
            "example": {
                "focus_intensity": 50,
                "target_bpm": 0
            }
        }

class FocusProcessingResponse(BaseModel):
    """Response model for focus processing submission"""
    job_id: str
    song_id: int
    estimated_duration_seconds: float
    message: str

class JobStatusResponse(BaseModel):
    """Response model for job status"""
    job_id: str
    status: str
    progress_percent: int
    current_step: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    estimated_completion: Optional[str] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

@focus_router.post("/process/{song_id}", response_model=FocusProcessingResponse)
async def start_focus_processing(
    song_id: int,
    request: FocusProcessingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start focus processing for a song
    
    This is the main endpoint users will call to transform their music
    
    Why async? Processing takes 2-3 minutes, so we return immediately with a job ID
    """
    logger.info(f"Focus processing requested for song {song_id}")
    
    # Validate song exists
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    
    # Check if song file exists
    audio_path = Path(settings.MUSIC_FOLDER) / song.filepath
    if not audio_path.exists():
        song.is_available = False
        db.commit()
        raise HTTPException(status_code=404, detail="Audio file not found on disk")
    
    # Validate processing parameters
    is_valid, error_msg = validate_processing_request(
        str(audio_path), 
        request.focus_intensity, 
        request.target_bpm
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Check if we already have a processed version with these exact parameters
    existing_version = db.query(ProcessedVersion).filter(
        ProcessedVersion.song_id == song_id,
        ProcessedVersion.focus_intensity == request.focus_intensity,
        ProcessedVersion.target_bpm == request.target_bpm
    ).first()
    
    if existing_version:
        # Check if the processed file still exists
        processed_path = Path(existing_version.processed_filepath)
        if processed_path.exists():
            logger.info(f"Using existing processed version for song {song_id}")
            # Return immediately with a mock job that's already "completed"
            return FocusProcessingResponse(
                job_id="cached",
                song_id=song_id,
                estimated_duration_seconds=0,
                message="Using cached processed version"
            )
    
    # Estimate processing time
    estimated_duration = estimate_processing_duration(song.duration or 180, request.focus_intensity)
    
    # Submit processing job
    job_id = submit_processing_job(
        song_id=song_id,
        input_file=str(audio_path),
        intensity=request.focus_intensity,
        target_bpm=request.target_bpm
    )
    
    logger.info(f"Submitted processing job {job_id} for song {song_id}")
    
    return FocusProcessingResponse(
        job_id=job_id,
        song_id=song_id,
        estimated_duration_seconds=estimated_duration,
        message=f"Processing started. Estimated completion in {estimated_duration:.0f} seconds"
    )

@focus_router.get("/job/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get status of a processing job
    
    Frontend will poll this endpoint to check progress
    """
    # Handle cached/existing processed versions
    if job_id == "cached":
        return JobStatusResponse(
            job_id="cached",
            status="completed",
            progress_percent=100,
            current_step="Using cached version",
            created_at="",
            result={"cached": True}
        )
    
    job_info = get_job_info(job_id)
    if not job_info:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatusResponse(**job_info)

@focus_router.delete("/job/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancel a processing job
    
    Useful if user changes their mind or wants to try different settings
    """
    if job_id == "cached":
        raise HTTPException(status_code=400, detail="Cannot cancel cached result")
    
    success = cancel_processing_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found or already completed")
    
    return {"message": f"Job {job_id} cancelled successfully"}

@focus_router.get("/job/{job_id}/download")
async def download_processed_audio(job_id: str, db: Session = Depends(get_db)):
    """
    Download the processed audio file
    
    Called after job is completed to get the focus-transformed audio
    """
    from fastapi.responses import FileResponse
    
    # Handle cached versions
    if job_id == "cached":
        raise HTTPException(
            status_code=400, 
            detail="Use /focus/download/{song_id} for cached versions"
        )
    
    job_info = get_job_info(job_id)
    if not job_info:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job_info['status'] != 'completed':
        raise HTTPException(
            status_code=400, 
            detail=f"Job not completed. Current status: {job_info['status']}"
        )
    
    if not job_info.get('result', {}).get('processed_file_path'):
        raise HTTPException(status_code=500, detail="Processed file path not found")
    
    processed_file_path = job_info['result']['processed_file_path']
    
    # Check if file exists
    if not Path(processed_file_path).exists():
        raise HTTPException(status_code=404, detail="Processed file not found on disk")
    
    # Save to database for future use
    song_id = job_info['song_id']
    intensity = job_info['result'].get('focus_intensity', 50)
    target_bpm = job_info['result'].get('processed_bpm', 0)
    
    # Create database record
    processed_version = ProcessedVersion(
        song_id=song_id,
        focus_intensity=intensity,
        target_bpm=target_bpm,
        processed_filepath=processed_file_path,
        processed_duration=job_info['result'].get('processed_duration'),
        actual_bpm=job_info['result'].get('processed_bpm'),
        file_size=Path(processed_file_path).stat().st_size
    )
    
    db.add(processed_version)
    db.commit()
    
    # Get original song for filename
    song = db.query(Song).filter(Song.id == song_id).first()
    filename = f"{song.title if song else 'song'}_focus_{intensity}%.mp3"
    
    return FileResponse(
        processed_file_path,
        media_type="audio/mpeg",
        filename=filename,
        headers={
            "Cache-Control": "public, max-age=3600",
        }
    )

@focus_router.get("/download/{song_id}")
async def download_cached_processed_audio(
    song_id: int,
    intensity: int,
    target_bpm: int = 0,
    db: Session = Depends(get_db)
):
    """
    Download cached processed audio directly
    
    For cases where we already have the processed version
    """
    from fastapi.responses import FileResponse
    
    # Find existing processed version
    processed_version = db.query(ProcessedVersion).filter(
        ProcessedVersion.song_id == song_id,
        ProcessedVersion.focus_intensity == intensity,
        ProcessedVersion.target_bpm == target_bpm
    ).first()
    
    if not processed_version:
        raise HTTPException(status_code=404, detail="Processed version not found")
    
    processed_path = Path(processed_version.processed_filepath)
    if not processed_path.exists():
        # Clean up database record
        db.delete(processed_version)
        db.commit()
        raise HTTPException(status_code=404, detail="Processed file not found on disk")
    
    # Get song info for filename
    song = db.query(Song).filter(Song.id == song_id).first()
    filename = f"{song.title if song else 'song'}_focus_{intensity}%.mp3"
    
    return FileResponse(
        processed_version.processed_filepath,
        media_type="audio/mpeg",
        filename=filename
    )

@focus_router.get("/analyze/{song_id}")
async def analyze_song_for_focus(song_id: int, db: Session = Depends(get_db)):
    """
    Analyze a song to provide focus processing recommendations
    
    Helps users choose optimal focus intensity and target BPM
    """
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    
    audio_path = Path(settings.MUSIC_FOLDER) / song.filepath
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    # Perform audio analysis
    analysis = AudioAnalyzer.analyze_audio_file(str(audio_path))
    
    if 'error' in analysis:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {analysis['error']}")
    
    # Generate recommendations based on analysis
    recommendations = _generate_focus_recommendations(analysis)
    
    return {
        'song_id': song_id,
        'analysis': analysis,
        'recommendations': recommendations
    }

@focus_router.get("/queue/status")
async def get_queue_status():
    """
    Get current processing queue status
    
    Useful for monitoring system load and queue length
    """
    queue = get_processing_queue()
    queue_info = queue.get_queue_info()
    
    return {
        'queue_info': queue_info,
        'system_status': 'healthy' if queue_info['running'] < queue_info['max_concurrent'] else 'busy'
    }

def _generate_focus_recommendations(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate focus processing recommendations based on audio analysis
    
    This helps users choose optimal settings for their music
    """
    tempo = analysis.get('tempo', 120)
    complexity = analysis.get('processing_complexity', 'medium')
    dynamic_range = analysis.get('dynamic_range', 0.5)
    
    recommendations = {
        'recommended_intensity': 50,  # Default
        'recommended_target_bpm': 0,  # Auto
        'reasoning': []
    }
    
    # Tempo-based recommendations
    if tempo > 140:
        recommendations['recommended_intensity'] = 70
        recommendations['recommended_target_bpm'] = max(80, tempo * 0.6)
        recommendations['reasoning'].append("Fast tempo detected - higher intensity recommended")
    elif tempo < 80:
        recommendations['recommended_intensity'] = 30
        recommendations['reasoning'].append("Slow tempo detected - lower intensity sufficient")
    
    # Complexity-based recommendations
    if complexity == 'high':
        recommendations['recommended_intensity'] = min(80, recommendations['recommended_intensity'] + 20)
        recommendations['reasoning'].append("Complex audio - higher intensity for better focus")
    elif complexity == 'low':
        recommendations['recommended_intensity'] = max(25, recommendations['recommended_intensity'] - 15)
        recommendations['reasoning'].append("Simple audio - lower intensity preserves musicality")
    
    # Dynamic range considerations
    if dynamic_range > 0.6:
        recommendations['reasoning'].append("High dynamic range - processing will smooth energy levels")
    
    return recommendations

# Why this API design:
# 1. RESTful endpoints - intuitive URL structure
# 2. Async processing - handles long-running operations gracefully
# 3. Job tracking - users can monitor progress
# 4. Caching - avoid reprocessing identical requests
# 5. Validation - prevents invalid inputs
# 6. Error handling - clear error messages for debugging
# 7. Recommendations - helps users choose optimal settings