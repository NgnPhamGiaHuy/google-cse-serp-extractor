from datetime import datetime
from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class SearchJobStatus(BaseModel):
    """Status of a search job"""
    job_id: str
    status: Literal["pending", "running", "completed", "failed"]
    progress: int = Field(ge=0, le=100, description="Progress percentage")
    total_keywords: int
    completed_keywords: int
    results_count: int = 0
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    # Enhanced progress tracking
    current_stage: Optional[str] = None
    stage_progress: Optional[int] = None
    estimated_time_remaining: Optional[int] = None  # seconds
    current_keyword: Optional[str] = None
    processing_speed: Optional[float] = None  # keywords per minute
    last_updated: Optional[datetime] = None
    
    # Additional metadata
    metadata: Optional[Dict[str, Any]] = None
    
    # Quota error tracking
    quota_error: Optional[Dict[str, Any]] = None
    quota_exceeded: bool = False


