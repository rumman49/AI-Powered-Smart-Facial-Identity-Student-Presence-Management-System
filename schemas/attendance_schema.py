from datetime import date as DateType, time as TimeType
from typing import Optional
from pydantic import BaseModel

class AttendanceMarkRequest(BaseModel):
    student_id: int
    confidence_score: Optional[float] = None
    attendance_session_id: Optional[int] = None  # Add this field

class AttendanceResponse(BaseModel):
    id: int
    student_id: int
    date: DateType
    time: TimeType
    status: str
    confidence_score: Optional[float] = None
    attendance_session_id: Optional[int] = None  # Added

    class Config:
        from_attributes = True