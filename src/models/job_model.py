from sqlalchemy import Column, DateTime, Integer, String, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from src.services.postgres_handler import Base
from datetime import datetime

class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    recruiter_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String)
    parsed_jd = Column(JSON)
    jd_vector = Column(JSON)
    required_experience = Column(Integer)  # in months
    is_active = Column(Boolean, default=True)
    mongodb_id = Column(String)  # Reference to MongoDB document
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationship with User model
    recruiter = relationship("User", back_populates="posted_jobs")