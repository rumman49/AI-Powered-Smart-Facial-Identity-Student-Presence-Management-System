import enum
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import TypeDecorator
from database.connection import Base

class StudentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"

class StudentStatusType(TypeDecorator):
    """Safely handles case conversions between MySQL and Python Enum."""
    impl = String(20)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if isinstance(value, StudentStatus):
            return value.value
        if isinstance(value, str):
            return value.upper()
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            try:
                return StudentStatus(value.upper())
            except ValueError:
                return StudentStatus.ACTIVE
        return value

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    mobile = Column(String(20), nullable=True)
    course = Column(String(100), nullable=True)
    semester = Column(String(20), nullable=True)
    department = Column(String(100), nullable=False)
    status = Column(StudentStatusType, default=StudentStatus.ACTIVE)
    profile_image = Column(String(255), nullable=True)
    
    # Missing date columns required by Pydantic response schema
    registration_date = Column(DateTime, server_default=func.now(), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, onupdate=func.now(), nullable=True)

    # Relationships
    face_encodings = relationship("FaceEncoding", back_populates="student")
    attendance_records = relationship("Attendance", back_populates="student")