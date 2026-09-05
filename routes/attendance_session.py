from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from database.connection import get_db
from models.attendance_session import AttendanceSession
from schemas.attendance_session import SessionCreate, SessionResponse

router = APIRouter(prefix="/api/sessions", tags=["Attendance Sessions"])

@router.post("/start", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def start_session(payload: SessionCreate, db: Session = Depends(get_db)):
    # Deactivate any currently active sessions
    db.query(AttendanceSession).filter(AttendanceSession.is_active == True).update({"is_active": False})
    
    new_session = AttendanceSession(title=payload.title, is_active=True)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

@router.post("/{session_id}/end", response_model=SessionResponse)
def end_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(AttendanceSession).filter(AttendanceSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.is_active = False
    session.ended_at = datetime.utcnow()
    db.commit()
    db.refresh(session)
    return session

@router.get("/active", response_model=Optional[SessionResponse])
def get_active_session(db: Session = Depends(get_db)):
    return db.query(AttendanceSession).filter(AttendanceSession.is_active == True).first()