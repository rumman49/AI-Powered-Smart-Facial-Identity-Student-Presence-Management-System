from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database.connection import engine, Base
import models

# 1. Import attendance router alongside auth, students, face
from routes import auth, students, face, attendance
from routes import attendance_session
from routes import face

Base.metadata.create_all(bind=engine)

uploads_dir = Path("uploads")
uploads_dir.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="NeuraForge API",
    description="AI-Powered Smart Facial Identity & Student Presence Management System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(students.router)
app.include_router(face.router)
# 2. Register attendance router
app.include_router(attendance.router)

app.mount("/uploads", StaticFiles(directory=uploads_dir.as_posix()), name="uploads")

@app.get("/")
def home():
    return {"message": "NeuraForge API is running cleanly!"}

app.include_router(attendance_session.router)
# Include router
app.include_router(face.router)