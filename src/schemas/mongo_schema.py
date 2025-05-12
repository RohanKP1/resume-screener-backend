from typing import Dict, Optional
from datetime import datetime
from pydantic import BaseModel

class ResumeDocument(BaseModel):
    user_id: int
    raw_text: str
    file_name: str
    file_type: str
    created_at: datetime = datetime.utcnow()
    metadata: Optional[Dict] = None

# Add to existing file
class JobDocument(BaseModel):
    recruiter_id: int
    raw_text: str
    title: str
    company: str
    created_at: datetime = datetime.utcnow()
    metadata: Optional[Dict] = None    