from datetime import date, datetime
from typing import Optional, Tuple
from models.attendance import Attendance
from models.attendance_session import AttendanceSession
from models.student import Student
from sqlalchemy.orm import Session


class AttendanceService:

    def mark_daily_attendance(
        self,
        db: Session,
        student_id: int,
        confidence_score: Optional[float] = None,
        attendance_session_id: Optional[int] = None,
    ) -> Tuple[Optional[Attendance], str]:
        today = date.today()

        # 1. Check if student exists
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return None, "STUDENT_NOT_FOUND"

        # 2. Auto-detect active session if no session ID was passed in request
        if not attendance_session_id:
            active_session = (
                db.query(AttendanceSession)
                .filter(AttendanceSession.is_active == True)
                .first()
            )
            if active_session:
                attendance_session_id = active_session.id

        # 3. Check for duplicate record
        # Checks duplicate per session if session exists, otherwise checks per date
        query = db.query(Attendance).filter(Attendance.student_id == student_id)
        if attendance_session_id:
            existing_record = query.filter(
                Attendance.attendance_session_id == attendance_session_id
            ).first()
        else:
            existing_record = query.filter(
                Attendance.date == today,
                Attendance.attendance_session_id == None
            ).first()

        if existing_record:
            return existing_record, "ALREADY_MARKED"

        # 4. Save attendance record
        new_record = Attendance(
            student_id=student_id,
            attendance_session_id=attendance_session_id,
            date=today,
            time=datetime.now().time().replace(microsecond=0),
            status="PRESENT",
            confidence_score=confidence_score,
        )

        db.add(new_record)
        db.commit()
        db.refresh(new_record)

        return new_record, "SUCCESS"