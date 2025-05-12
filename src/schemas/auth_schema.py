from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum

class UserType(str, Enum):
    CANDIDATE = "candidate"
    RECRUITER = "recruiter"

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    user_type: UserType

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    user_type: UserType

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user_type: UserType  # Add user type
    username: str  # Add username
    email: str
    user_id: int  # Add user ID