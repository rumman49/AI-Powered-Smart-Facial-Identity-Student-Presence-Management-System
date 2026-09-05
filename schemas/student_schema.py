from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from models.student import StudentStatus
import enum

class StudentCreate(BaseModel):
    student_code: str
    name: str
    email: EmailStr
    mobile: str
    course: str
    semester: str
    department: str

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile: Optional[str] = None
    course: Optional[str] = None
    semester: Optional[str] = None
    department: Optional[str] = None
    status: Optional[StudentStatus] = None

# schemas/student_schema.py
class StudentResponse(BaseModel):
    id: int
    student_code: str
    name: str
    email: str
    department: str
    mobile: Optional[str] = None
    course: Optional[str] = None
    semester: Optional[str] = None
    status: StudentStatus
    profile_image: Optional[str] = None  # Stores portable relative path

    class Config:
        from_attributes = True

class StudentListResponse(BaseModel):
    students: List[StudentResponse]
    total: int
    skip: int
    limit: int
    
class StudentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"