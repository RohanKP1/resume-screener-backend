from sqlalchemy import Column, DateTime, Integer, String, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from src.services.postgres_handler import Base
from datetime import datetime

class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    parsed_resume = Column(JSON)
    resume_vector = Column(JSON)
    total_experience = Column(JSON)
    mongodb_id = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    # Remove location_vector column since we're using text-based matching
    
    user = relationship("User", back_populates="candidate_profile")