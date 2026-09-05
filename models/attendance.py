from datetime import date, datetime
from sqlalchemy import Column, Integer, ForeignKey, Date, Time, Float, String, UniqueConstraint
from sqlalchemy.orm import relationship
from database.connection import Base

class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    attendance_session_id = Column(Integer, ForeignKey("attendance_sessions.id"), nullable=True, index=True)
    date = Column(Date, default=date.today, nullable=False, index=True)
    time = Column(Time, default=lambda: datetime.now().time().replace(microsecond=0), nullable=False)
    status = Column(String(20), default="PRESENT", nullable=False)
    confidence_score = Column(Float, nullable=True)

    # Relationships
    student = relationship("Student", back_populates="attendance_records")  # N Records -> 1 Student
    session = relationship("AttendanceSession", back_populates="attendance_records")  # N Records -> 1 Session

    # Ensures a student can only be marked ONCE per session (or once per date if session is NULL)
    __table_args__ = (
        UniqueConstraint('student_id', 'attendance_session_id', name='uq_student_session_attendance'),
    )