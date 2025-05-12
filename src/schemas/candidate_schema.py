from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime

class CandidateProfileBase(BaseModel):
    """Base schema for candidate profile data."""
    parsed_resume: Optional[Dict] = None
    total_experience: Optional[float] = None  # Changed to float for years
    mongodb_id: Optional[str] = None

class CandidateProfileCreate(CandidateProfileBase):
    """Schema for creating a candidate profile."""
    user_id: int

class CandidateProfileUpdate(CandidateProfileBase):
    """Schema for updating a candidate profile."""
    pass

class CandidateProfileResponse(CandidateProfileBase):
    """Schema for candidate profile responses."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    raw_text: Optional[str] = None
    
    class Config:
        from_attributes = True
        # Exclude resume_vector from response
        exclude = {"resume_vector", "location_vector"}

class SearchScores(BaseModel):
    """Schema for search match scores"""
    skills_score: float
    location_score: float
    experience_score: float
    total_score: float

class CandidateSearchResponse(CandidateProfileResponse):
    """Schema for search results"""
    match_scores: Optional[SearchScores] = None
    
    class Config:
        from_attributes = True
        # Exclude vectors from response
        exclude = {"resume_vector", "location_vector"}

# Add new schema for ranking scores
class RankScores(BaseModel):
    """Schema for ranking match scores"""
    skills_score: float
    experience_score: float
    location_score: float
    total_score: float

class CandidateRankResponse(CandidateProfileResponse):
    """Schema for ranking results"""
    match_scores: Optional[RankScores] = None
    
    class Config:
        from_attributes = True
        exclude = {"resume_vector"}
