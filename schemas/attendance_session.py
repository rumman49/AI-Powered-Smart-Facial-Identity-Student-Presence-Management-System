from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SessionCreate(BaseModel):
    title: str

class SessionResponse(BaseModel):
    id: int
    title: str
    is_active: bool
    created_at: datetime
    ended_at: Optional[datetime] = None

    class Config:
        from_attributes = True