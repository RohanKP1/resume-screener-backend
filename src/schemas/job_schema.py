from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime

class JobBase(BaseModel):
    """Base schema for job data."""
    title: str
    company: str
    location: Optional[str] = None
    required_experience: float  # Changed to float for years

class JobCreate(JobBase):
    """Schema for creating a job."""
    job_description: str  # Raw job description text

class JobUpdate(JobBase):
    """Schema for updating a job."""
    is_active: Optional[bool] = None

class JobResponse(JobBase):
    """Schema for job responses."""
    id: int
    recruiter_id: int
    parsed_jd: Dict
    is_active: bool
    created_at: datetime
    updated_at: datetime
    raw_text: Optional[str] = None  # Added for API responses that include MongoDB data

    class Config:
        from_attributes = True