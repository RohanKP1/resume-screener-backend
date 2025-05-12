from sqlalchemy import Column, Integer, String, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from src.services.postgres_handler import Base
import enum

class UserType(str, enum.Enum):
    CANDIDATE = "candidate"
    RECRUITER = "recruiter"

class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    user_type = Column(SQLAlchemyEnum(UserType, name='usertype', create_type=False), nullable=False)
    
    # Add relationship to CandidateProfile
    candidate_profile = relationship("CandidateProfile", back_populates="user", uselist=False)
    # Add to existing User class
    posted_jobs = relationship("Job", back_populates="recruiter")

    def __init__(self, **kwargs):
        if 'user_type' in kwargs and isinstance(kwargs['user_type'], UserType):
            kwargs['user_type'] = kwargs['user_type'].value
        super().__init__(**kwargs)