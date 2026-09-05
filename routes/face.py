import os
import pickle
import cv2
import numpy as np
import face_recognition
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from database.connection import get_db
from models.student import Student
from services.attendance_service import AttendanceService

router = APIRouter(prefix="/api/face", tags=["Face Recognition"])

ENCODING_FOLDER = "data/encodings"
FACE_THRESHOLD = 0.52
MAX_SAMPLES = 30
os.makedirs(ENCODING_FOLDER, exist_ok=True)

attendance_service = AttendanceService()


def load_encodings():
    known_encodings, known_ids, known_names = [], [], []
    if not os.path.exists(ENCODING_FOLDER):
        return np.empty((0, 128), dtype=np.float32), [], []

    for file_name in os.listdir(ENCODING_FOLDER):
        if not file_name.endswith(".pkl"):
            continue
        file_path = os.path.join(ENCODING_FOLDER, file_name)
        try:
            with open(file_path, "rb") as file:
                data = pickle.load(file)
            for encoding in data["encodings"]:
                known_encodings.append(np.asarray(encoding, dtype=np.float32))
                known_ids.append(data["id"])
                known_names.append(data["name"])
        except Exception as e:
            print(f"Error loading {file_name}: {e}")

    known_encodings = (
        np.asarray(known_encodings, dtype=np.float32)
        if known_encodings
        else np.empty((0, 128), dtype=np.float32)
    )
    return known_encodings, known_ids, known_names


@router.post("/enroll")
async def enroll_student(
    person_id: int = Form(...),
    person_name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Verify student exists in MySQL database first
    student = db.query(Student).filter(Student.id == person_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student ID not found in database.")

    image_bytes = await file.read()
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if frame is None:
        return {"status": "failed", "message": "Invalid image"}

    small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
    rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb_frame, model="hog")
    if not face_locations:
        return {"status": "failed", "message": "No face detected"}

    face_encodings = face_recognition.face_encodings(rgb_frame, [face_locations[0]], num_jitters=1)
    if not face_encodings:
        return {"status": "failed", "message": "Face encoding failed"}

    file_path = os.path.join(ENCODING_FOLDER, f"{person_id}.pkl")
    encodings = []

    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            old_data = pickle.load(f)
            encodings = old_data.get("encodings", [])

    if len(encodings) >= MAX_SAMPLES:
        return {"status": "already_complete", "message": "Maximum encodings reached"}

    encodings.append(face_encodings[0])
    with open(file_path, "wb") as f:
        pickle.dump({"id": str(person_id), "name": person_name, "encodings": encodings}, f)

    return {"status": "enrolled", "student_id": person_id, "samples": len(encodings)}


@router.post("/recognize")
async def recognize_and_mark(
    file: UploadFile = File(...),
    session_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    image_bytes = await file.read()
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if frame is None:
        return {"status": "error", "message": "Invalid image"}

    small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
    rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame, model="hog")

    if not face_locations:
        return {"faces": []}

    known_encodings, known_ids, known_names = load_encodings()
    results = []

    for face_location in face_locations:
        face_encodings = face_recognition.face_encodings(rgb_frame, [face_location], num_jitters=1)
        if not face_encodings or len(known_encodings) == 0:
            results.append({"status": "STRANGER"})
            continue

        face_encoding = np.asarray(face_encodings[0], dtype=np.float32)
        distances = np.linalg.norm(known_encodings - face_encoding, axis=1)
        best_index = np.argmin(distances)
        best_distance = distances[best_index]

        if best_distance <= FACE_THRESHOLD:
            student_id = int(known_ids[best_index])
            confidence = round(float(1 - best_distance), 2)

            # Auto-mark attendance in MySQL database
            record, mark_status = attendance_service.mark_daily_attendance(
                db=db,
                student_id=student_id,
                confidence_score=confidence,
                attendance_session_id=session_id
            )

            results.append({
                "student_id": student_id,
                "name": known_names[best_index],
                "status": "PRESENT",
                "attendance_db_status": mark_status,
                "confidence": confidence
            })
        else:
            results.append({"status": "STRANGER"})

    return {"faces": results}