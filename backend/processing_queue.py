# backend/processing_queue.py

import asyncio
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional, Any, Callable
from dataclasses import dataclass, field
import logging
from pathlib import Path
import threading
import time

logger = logging.getLogger(__name__)

class JobStatus(Enum):
    """
    Processing job status enumeration
    
    Why an enum? Type safety and clear state management
    """
    PENDING = "pending"       # Job created, waiting to start
    RUNNING = "running"       # Currently processing
    COMPLETED = "completed"   # Successfully finished
    FAILED = "failed"        # Processing failed
    CANCELLED = "cancelled"   # User cancelled

@dataclass
class ProcessingJob:
    """
    Represents a focus processing job
    
    Why dataclass? Clean data structure with automatic methods
    """
    job_id: str
    song_id: int
    input_file_path: str
    focus_intensity: int
    target_bpm: int
    created_at: datetime = field(default_factory=datetime.now)
    status: JobStatus = JobStatus.PENDING
    
    # Progress tracking
    progress_percent: int = 0
    current_step: str = "Initializing"
    
    # Results
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for API responses"""
        return {
            'job_id': self.job_id,
            'song_id': self.song_id,
            'status': self.status.value,
            'progress_percent': self.progress_percent,
            'current_step': self.current_step,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'estimated_completion': self.estimated_completion.isoformat() if self.estimated_completion else None,
            'error_message': self.error_message,
            'result': self.result
        }

class ProcessingQueue:
    """
    Simple in-memory queue for processing jobs
    
    Why not a full queue system like Celery?
    - For MVP, in-memory is simpler
    - No external dependencies (Redis, etc.)
    - Easy to understand and debug
    - Can upgrade to full queue system later
    
    For production, consider:
    - Redis + Celery for distributed processing
    - RabbitMQ for message queuing
    - Database job storage for persistence
    """
    
    def __init__(self, max_concurrent_jobs: int = 2):
        """
        Initialize processing queue
        
        Args:
            max_concurrent_jobs: Maximum simultaneous processing jobs
                                (2 is reasonable for local development)
        """
        self.jobs: Dict[str, ProcessingJob] = {}
        self.max_concurrent_jobs = max_concurrent_jobs
        self.running_jobs: Dict[str, asyncio.Task] = {}
        self._lock = threading.Lock()
        
        # Start background worker
        self._worker_task = None
        self._should_stop = False
        
    async def start_worker(self):
        """Start the background worker that processes jobs"""
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._worker_loop())
            logger.info("Processing queue worker started")
    
    async def stop_worker(self):
        """Stop the background worker"""
        self._should_stop = True
        if self._worker_task:
            await self._worker_task
            logger.info("Processing queue worker stopped")
    
    def submit_job(self, song_id: int, input_file_path: str, 
                   focus_intensity: int, target_bpm: int = 0) -> str:
        """
        Submit a new processing job
        
        Returns:
            job_id: Unique identifier for tracking the job
        """
        job_id = str(uuid.uuid4())
        
        job = ProcessingJob(
            job_id=job_id,
            song_id=song_id,
            input_file_path=input_file_path,
            focus_intensity=focus_intensity,
            target_bpm=target_bpm
        )
        
        with self._lock:
            self.jobs[job_id] = job
        
        logger.info(f"Submitted processing job {job_id} for song {song_id}")
        return job_id
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a job"""
        with self._lock:
            job = self.jobs.get(job_id)
            return job.to_dict() if job else None
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a pending or running job
        
        Returns:
            True if job was cancelled, False if not found or already completed
        """
        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                return False
            
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                return False  # Already finished
            
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.now()
            
            # Cancel running task if exists
            if job_id in self.running_jobs:
                self.running_jobs[job_id].cancel()
                del self.running_jobs[job_id]
            
            logger.info(f"Cancelled job {job_id}")
            return True
    
    def get_queue_info(self) -> Dict[str, Any]:
        """Get information about the current queue state"""
        with self._lock:
            pending = sum(1 for job in self.jobs.values() if job.status == JobStatus.PENDING)
            running = sum(1 for job in self.jobs.values() if job.status == JobStatus.RUNNING)
            completed = sum(1 for job in self.jobs.values() if job.status == JobStatus.COMPLETED)
            failed = sum(1 for job in self.jobs.values() if job.status == JobStatus.FAILED)
            
            return {
                'total_jobs': len(self.jobs),
                'pending': pending,
                'running': running,
                'completed': completed,
                'failed': failed,
                'max_concurrent': self.max_concurrent_jobs
            }
    
    async def _worker_loop(self):
        """
        Background worker that processes queued jobs
        
        This runs continuously and picks up pending jobs
        """
        logger.info("Processing worker loop started")
        
        while not self._should_stop:
            try:
                # Check for pending jobs to process
                pending_jobs = []
                with self._lock:
                    for job in self.jobs.values():
                        if job.status == JobStatus.PENDING:
                            pending_jobs.append(job)
                
                # Start jobs up to max concurrent limit
                current_running = len(self.running_jobs)
                can_start = self.max_concurrent_jobs - current_running
                
                for job in pending_jobs[:can_start]:
                    task = asyncio.create_task(self._process_job(job))
                    self.running_jobs[job.job_id] = task
                    logger.info(f"Started processing job {job.job_id}")
                
                # Clean up completed tasks
                completed_job_ids = []
                for job_id, task in self.running_jobs.items():
                    if task.done():
                        completed_job_ids.append(job_id)
                
                for job_id in completed_job_ids:
                    del self.running_jobs[job_id]
                
                # Wait a bit before checking again
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                await asyncio.sleep(5.0)  # Wait longer on error
    
    async def _process_job(self, job: ProcessingJob):
        """
        Process a single job
        
        This is where the actual audio processing happens
        """
        try:
            logger.info(f"Processing job {job.job_id} started")
            
            # Update job status
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now()
            job.current_step = "Starting processing..."
            
            # Import here to avoid circular imports
            from focus_processor import process_song_for_focus
            from audio_utils import estimate_processing_duration
            
            # Estimate completion time
            from audio_utils import AudioAnalyzer
            analysis = AudioAnalyzer.analyze_audio_file(job.input_file_path)
            estimated_duration = estimate_processing_duration(
                analysis.get('duration', 180), job.focus_intensity
            )
            job.estimated_completion = datetime.now() + timedelta(seconds=estimated_duration)
            
            # Progress tracking function
            def update_progress(step: str, percent: int):
                job.current_step = step
                job.progress_percent = percent
                logger.debug(f"Job {job.job_id}: {step} ({percent}%)")
            
            # Process the audio (this is the long-running operation)
            update_progress("Loading audio...", 10)
            await asyncio.sleep(0.1)  # Yield control
            
            update_progress("Separating vocals and instruments...", 20)
            await asyncio.sleep(0.1)
            
            # Run the actual processing in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                process_song_for_focus,
                job.input_file_path,
                job.focus_intensity,
                job.target_bpm
            )
            
            update_progress("Finalizing...", 90)
            
            if result.get('success', False):
                job.status = JobStatus.COMPLETED
                job.result = result
                job.progress_percent = 100
                job.current_step = "Complete"
                logger.info(f"Job {job.job_id} completed successfully")
            else:
                job.status = JobStatus.FAILED
                job.error_message = result.get('error', 'Unknown error')
                logger.error(f"Job {job.job_id} failed: {job.error_message}")
            
        except asyncio.CancelledError:
            job.status = JobStatus.CANCELLED
            job.error_message = "Job was cancelled"
            logger.info(f"Job {job.job_id} was cancelled")
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            logger.error(f"Job {job.job_id} failed with exception: {e}")
        
        finally:
            job.completed_at = datetime.now()

# Global queue instance
_queue_instance = None

def get_processing_queue() -> ProcessingQueue:
    """
    Get or create global processing queue
    
    Singleton pattern for simple job management
    """
    global _queue_instance
    if _queue_instance is None:
        _queue_instance = ProcessingQueue()
    return _queue_instance

async def initialize_queue():
    """Initialize the processing queue (call at app startup)"""
    queue = get_processing_queue()
    await queue.start_worker()

async def shutdown_queue():
    """Shutdown the processing queue (call at app shutdown)"""
    queue = get_processing_queue()
    await queue.stop_worker()

# Convenience functions for API use
def submit_processing_job(song_id: int, input_file: str, 
                         intensity: int, target_bpm: int = 0) -> str:
    """Submit a new processing job and return job ID"""
    queue = get_processing_queue()
    return queue.submit_job(song_id, input_file, intensity, target_bpm)

def get_job_info(job_id: str) -> Optional[Dict[str, Any]]:
    """Get job status and information"""
    queue = get_processing_queue()
    return queue.get_job_status(job_id)

def cancel_processing_job(job_id: str) -> bool:
    """Cancel a processing job"""
    queue = get_processing_queue()
    return queue.cancel_job(job_id)

if __name__ == "__main__":
    # Test the queue system
    async def test_queue():
        queue = ProcessingQueue()
        await queue.start_worker()
        
        # This would normally be a real audio file
        job_id = queue.submit_job(
            song_id=1,
            input_file_path="/path/to/test.mp3", 
            focus_intensity=50
        )
        
        print(f"Submitted job: {job_id}")
        
        # Monitor job progress
        for i in range(10):
            status = queue.get_job_status(job_id)
            print(f"Job status: {status['status']} - {status['current_step']}")
            await asyncio.sleep(2)
            
            if status['status'] in ['completed', 'failed', 'cancelled']:
                break
        
        await queue.stop_worker()
    
    asyncio.run(test_queue())

# Why this design:
# 1. Async processing - doesn't block API responses
# 2. Progress tracking - users can see what's happening
# 3. Job cancellation - users can stop long-running jobs
# 4. Error handling - graceful failure recovery
# 5. Resource limits - prevents system overload
# 6. Simple but extensible - easy to upgrade to full queue system later