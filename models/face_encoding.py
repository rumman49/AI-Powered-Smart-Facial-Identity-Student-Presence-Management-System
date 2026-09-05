from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base

class FaceEncoding(Base):
    __tablename__ = "face_encodings"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    encoding_vector = Column(LargeBinary, nullable=False)  # Stored as JSON/bytes
    image_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    student = relationship("Student", back_populates="face_encodings")