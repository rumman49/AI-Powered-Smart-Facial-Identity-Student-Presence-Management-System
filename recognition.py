import os
import pickle
import time
import cv2
import face_recognition
import numpy as np
import requests

# ==========================================
# SETTINGS
# ==========================================

ENCODING_FOLDER = "data/encodings"

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# Recognition every 3rd frame
RECOGNITION_INTERVAL = 3

# Face matching threshold
FACE_THRESHOLD = 0.52

# Keep result temporarily if face disappears
MAX_LOST_FRAMES = 20

# API Configuration
API_MARK_URL = "http://127.0.0.1:8000/api/attendance/mark"
COOLDOWN_SECONDS = 10  # Seconds before allowing re-scan for same student

# Track last scan timestamps per student
last_scanned = {}

# ==========================================
# LOAD ENROLLED FACE DATA
# ==========================================

known_encodings = []
known_ids = []
known_names = []

print("\n================================")
print("LOADING FACE DATA")
print("================================")

if not os.path.exists(ENCODING_FOLDER):
    print("Encoding folder not found!")
    exit()

# Load all PKL files
for file_name in os.listdir(ENCODING_FOLDER):
    if not file_name.endswith(".pkl"):
        continue

    file_path = os.path.join(ENCODING_FOLDER, file_name)

    try:
        with open(file_path, "rb") as file:
            data = pickle.load(file)

        person_id = data["id"]
        person_name = data["name"]

        for encoding in data["encodings"]:
            known_encodings.append(np.asarray(encoding, dtype=np.float32))
            known_ids.append(person_id)
            known_names.append(person_name)

        print(
            f"Loaded: {person_id} - {person_name} ({len(data['encodings'])} encodings)"
        )

    except Exception as e:
        print(f"Error loading {file_name}: {e}")

# Convert to NumPy array
if len(known_encodings) > 0:
    known_encodings = np.asarray(known_encodings, dtype=np.float32)
else:
    known_encodings = np.empty((0, 128), dtype=np.float32)

print("\n================================")
print("FACE DATA LOADED")
print("Total encodings:", len(known_encodings))
print("================================")


# ==========================================
# RECOGNITION FUNCTION
# ==========================================


def recognize_face(rgb_frame, face_location):
    face_encodings = face_recognition.face_encodings(
        rgb_frame, [face_location], num_jitters=1
    )

    if not face_encodings:
        return None

    face_encoding = np.asarray(face_encodings[0], dtype=np.float32)

    if len(known_encodings) == 0:
        return None

    distances = np.linalg.norm(known_encodings - face_encoding, axis=1)
    best_index = np.argmin(distances)
    best_distance = distances[best_index]

    if best_distance <= FACE_THRESHOLD:
        return (known_ids[best_index], known_names[best_index], best_distance)

    return None


# ==========================================
# CAMERA SETUP
# ==========================================

camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

if not camera.isOpened():
    print("Camera could not be opened!")
    exit()

frame_count = 0
last_faces = []
lost_face_count = 0

print("\n================================")
print("FACE RECOGNITION STARTED")
print("================================")
print("Press ESC to exit.\n")

# ==========================================
# MAIN LOOP
# ==========================================

while True:
    ret, frame = camera.read()
    if not ret:
        print("Camera frame could not be read.")
        break

    frame_count += 1

    # Process every Nth frame
    if frame_count % RECOGNITION_INTERVAL == 0:
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(
            rgb_frame, model="hog"
        )

        if face_locations:
            lost_face_count = 0
            current_faces = []

            for face_location in face_locations:
                result = recognize_face(rgb_frame, face_location)

                if result is not None:
                    person_id = result[0]
                    person_name = result[1]
                    distance = result[2]
                    status = "PRESENT"

                    # --------------------------------------------------
                    # API INTEGRATION & COOLDOWN LOGIC
                    # --------------------------------------------------
                    current_time = time.time()
                    try:
                        student_id_int = int(person_id)
                        if student_id_int not in last_scanned or (
                            current_time - last_scanned[student_id_int]
                        ) > COOLDOWN_SECONDS:
                            confidence = round(float(1 - distance), 2)
                            response = requests.post(
                                API_MARK_URL,
                                json={
                                    "student_id": student_id_int,
                                    "confidence_score": confidence,
                                },
                                timeout=2,
                            )
                            if response.status_code == 200:
                                print(
                                    f"[API SUCCESS] Marked attendance for Student ID {student_id_int}"
                                )
                                last_scanned[student_id_int] = current_time
                            else:
                                print(
                                    f"[API WARN] HTTP {response.status_code}: {response.text}"
                                )
                    except ValueError:
                        pass
                    except Exception as e:
                        print(f"[API ERROR] Connection failed: {e}")

                else:
                    person_id = "Unknown"
                    person_name = "STRANGER"
                    status = "STRANGER"

                current_faces.append(
                    (face_location, person_id, person_name, status)
                )

            last_faces = current_faces

        else:
            lost_face_count += 1
            if lost_face_count > MAX_LOST_FRAMES:
                last_faces = []

    # Draw face overlays
    for face_data in last_faces:
        face_location, person_id, person_name, status = face_data
        top, right, bottom, left = face_location

        # Scale back 50% coordinates
        top *= 2
        right *= 2
        bottom *= 2
        left *= 2

        color = (0, 255, 0) if status == "PRESENT" else (0, 0, 255)

        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(
            frame,
            f"ID: {person_id}",
            (left, max(25, top - 45)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
        )
        cv2.putText(
            frame,
            f"Name: {person_name}",
            (left, max(50, top - 15)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
        )
        cv2.putText(
            frame,
            status,
            (left, bottom + 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            color,
            2,
        )

    cv2.imshow("Face Recognition", frame)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC to quit
        break

camera.release()
cv2.destroyAllWindows()

print("\n================================")
print("RECOGNITION STOPPED")
print("================================")