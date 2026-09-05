from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from models.student import Student, StudentStatus
from schemas.student_schema import StudentCreate, StudentUpdate

# Portable directory resolution — works across Windows, macOS, and Linux
UPLOAD_DIR = Path("uploads/students")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class StudentService:

    def get_student_by_email(self, email: str, db: Session) -> Optional[Student]:
        return db.query(Student).filter(Student.email == email).first()

    def get_student_by_code(self, code: str, db: Session) -> Optional[Student]:
        return db.query(Student).filter(Student.student_code == code).first()

    def create_student(
        self, 
        student_data: StudentCreate, 
        db: Session, 
        image_bytes: Optional[bytes] = None
    ) -> Student:
        data = student_data.model_dump()
        
        # Ensure status is assigned as a valid StudentStatus enum value
        if isinstance(data.get("status"), str):
            data["status"] = StudentStatus[data["status"].upper()]

        student = Student(**data)
        db.add(student)
        db.flush()  # Populates student.id before committing

        if image_bytes:
            # 1. Create file name based on unique student code
            file_name = f"{student.student_code}.jpg"
            file_path = UPLOAD_DIR / file_name
            
            # 2. Write physical file to local disk folder
            with open(file_path, "wb") as f:
                f.write(image_bytes)
            
            # 3. Store portable relative path with forward slashes in DB
            student.profile_image = file_path.as_posix()  # Stores "uploads/students/1001.jpg"

        db.commit()
        db.refresh(student)
        return student

    def get_students(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100, 
        search: Optional[str] = None, 
        department: Optional[str] = None, 
        status: Optional[str] = None
    ):
        query = db.query(Student)
        if search:
            query = query.filter(
                (Student.name.ilike(f"%{search}%")) | (Student.student_code.ilike(f"%{search}%"))
            )
        if department:
            query = query.filter(Student.department == department)
        if status:
            query = query.filter(Student.status == status)
        return query.offset(skip).limit(limit).all()

    def count_students(
        self, 
        db: Session, 
        search: Optional[str] = None, 
        department: Optional[str] = None
    ) -> int:
        query = db.query(Student)
        if search:
            query = query.filter(
                (Student.name.ilike(f"%{search}%")) | (Student.student_code.ilike(f"%{search}%"))
            )
        if department:
            query = query.filter(Student.department == department)
        return query.count()

    def deactivate_student(self, student_id: int, db: Session) -> bool:
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return False
        student.status = StudentStatus.INACTIVE
        db.commit()
        return True