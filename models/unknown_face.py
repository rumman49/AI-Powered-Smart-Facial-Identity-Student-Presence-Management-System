import enum
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base

class UnknownStatus(str, enum.Enum):
    UNKNOWN = "unknown"
    UNDER_REVIEW = "under_review"
    IDENTIFIED = "identified"
    IGNORED = "ignored"

class UnknownFace(Base):
    __tablename__ = "unknown_faces"

    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String(255), nullable=False)
    detected_at = Column(DateTime, server_default=func.now())
    confidence = Column(Float, nullable=True)
    camera_id = Column(String(50), nullable=True)
    status = Column(Enum(UnknownStatus), default=UnknownStatus.UNKNOWN)
    reviewed_by = Column(String(100), nullable=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    notes = Column(String(500), nullable=True)

    student = relationship("Student")