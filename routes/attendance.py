from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.connection import get_db
from schemas.attendance_schema import AttendanceMarkRequest, AttendanceResponse
from services.attendance_service import AttendanceService  # type: ignore[reportMissingImports]

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])
attendance_service = AttendanceService()

@router.post("/mark")
def mark_attendance(payload: AttendanceMarkRequest, db: Session = Depends(get_db)):
    record, result_status = attendance_service.mark_daily_attendance(
        db,
        student_id=payload.student_id,
        confidence_score=payload.confidence_score,
        attendance_session_id=payload.attendance_session_id  # Added
    )
    return {"record": record, "status": result_status}

    if result_status == "STUDENT_NOT_FOUND":
        raise HTTPException(status_code=404, detail="Student not found.")

    if result_status == "ALREADY_MARKED":
        raise HTTPException(
            status_code=400, 
            detail="Attendance has already been marked for this student today."
        )

    return record