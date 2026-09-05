from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from database.connection import get_db
from dependencies.auth import require_staff_role
from models.student import Student
from models.user import User
from schemas.student_schema import StudentCreate, StudentListResponse, StudentResponse, StudentUpdate
from services.student_service import StudentService

router = APIRouter(prefix="/api/students", tags=["Students"])
student_service = StudentService()


@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    student_code: str = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    department: str = Form(...),
    mobile: Optional[str] = Form(None),
    course: Optional[str] = Form(None),
    semester: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_role)
):
    """Creates a new student record with an optional photo (Restricted to Admins and Teachers)."""
    
    # 1. Validate uniqueness
    if student_service.get_student_by_email(email, db):
        raise HTTPException(status_code=400, detail="Student with this email already exists")
    
    if student_service.get_student_by_code(student_code, db):
        raise HTTPException(status_code=400, detail="Student with this code already exists")
    
    # 2. Validate image file if provided
    image_bytes = None
    if file:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Uploaded file must be an image (JPEG/PNG)")
        image_bytes = await file.read()

    # 3. Construct schema object
    student_data = StudentCreate(
        student_code=student_code,
        name=name,
        email=email,
        department=department,
        mobile=mobile,
        course=course,
        semester=semester
    )
    
    # 4. Delegate to service layer
    return student_service.create_student(student_data, db, image_bytes=image_bytes)


@router.get("/", response_model=StudentListResponse)
def get_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    department: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Fetches a list of students with optional search and department filters."""
    students = student_service.get_students(
        db, skip=skip, limit=limit, search=search, department=department, status=status
    )
    total = student_service.count_students(db, search=search, department=department)
    return {
        "students": students,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db)):
    """Retrieves single student details by ID."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.delete("/{student_id}")
def delete_student(
    student_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_role)
):
    """Deactivates a student record (Soft delete)."""
    success = student_service.deactivate_student(student_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"message": "Student deactivated successfully"}