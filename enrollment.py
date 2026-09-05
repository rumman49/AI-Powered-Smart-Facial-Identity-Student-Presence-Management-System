import cv2
import face_recognition
import os
import pickle


# ==========================================
# SETTINGS
# ==========================================

ENCODING_FOLDER = "data/encodings"

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# Every 5th frame will be processed
PROCESS_INTERVAL = 5

# Total face samples for one person
MAX_SAMPLES = 30


# ==========================================
# CREATE FOLDER
# ==========================================

os.makedirs(
    ENCODING_FOLDER,
    exist_ok=True
)


# ==========================================
# PERSON DETAILS
# ==========================================

person_id = input(
    "Enter Person ID: "
).strip()

person_name = input(
    "Enter Person Name: "
).strip()


# ==========================================
# CHECK ID
# ==========================================

file_path = os.path.join(
    ENCODING_FOLDER,
    f"{person_id}.pkl"
)


if os.path.exists(file_path):

    print("\nThis ID already exists!")

    choice = input(
        "Do you want to replace it? (y/n): "
    ).lower()

    if choice != "y":

        print("Enrollment cancelled.")
        exit()


# ==========================================
# CAMERA
# ==========================================

camera = cv2.VideoCapture(0)

camera.set(
    cv2.CAP_PROP_FRAME_WIDTH,
    CAMERA_WIDTH
)

camera.set(
    cv2.CAP_PROP_FRAME_HEIGHT,
    CAMERA_HEIGHT
)

camera.set(
    cv2.CAP_PROP_BUFFERSIZE,
    1
)


if not camera.isOpened():

    print("Camera could not be opened!")
    exit()


# ==========================================
# VARIABLES
# ==========================================

frame_count = 0
sample_count = 0

encodings = []


# ==========================================
# START
# ==========================================

print("\n================================")
print("FACE ENROLLMENT")
print("================================")

print("Move your face slowly:")

print("1. Front")
print("2. Left")
print("3. Right")
print("4. Up")
print("5. Down")

print("\nTry different angles naturally.")

print("\nPress ESC to stop.\n")


# ==========================================
# ENROLLMENT LOOP
# ==========================================

while True:

    ret, frame = camera.read()

    if not ret:

        print("Camera not working.")
        break


    frame_count += 1


    # ======================================
    # PROCESS EVERY 5TH FRAME
    # ======================================

    if frame_count % PROCESS_INTERVAL == 0:

        # Resize to 50%
        small_frame = cv2.resize(
            frame,
            (0, 0),
            fx=0.5,
            fy=0.5
        )


        # BGR -> RGB
        rgb_frame = cv2.cvtColor(
            small_frame,
            cv2.COLOR_BGR2RGB
        )


        # ==================================
        # FACE DETECTION
        # ==================================

        face_locations = face_recognition.face_locations(
            rgb_frame,
            model="hog"
        )


        # ==================================
        # FACE FOUND
        # ==================================

        if face_locations:

            # During enrollment use first face
            face_location = face_locations[0]


            # ==================================
            # FACE ENCODING
            # ==================================

            face_encodings = face_recognition.face_encodings(
                rgb_frame,
                [face_location],
                num_jitters=1
            )


            if face_encodings:

                encoding = face_encodings[0]

                encodings.append(encoding)

                sample_count += 1


                # ==================================
                # COORDINATES
                # ==================================

                top, right, bottom, left = face_location

                # Convert 50% coordinates
                # to original frame
                top *= 2
                right *= 2
                bottom *= 2
                left *= 2


                # ==================================
                # FACE BOX
                # ==================================

                cv2.rectangle(
                    frame,
                    (left, top),
                    (right, bottom),
                    (255, 0, 0),
                    2
                )


                # ==================================
                # ID
                # ==================================

                cv2.putText(
                    frame,
                    f"ID: {person_id}",
                    (
                        left,
                        max(30, top - 45)
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )


                # ==================================
                # NAME
                # ==================================

                cv2.putText(
                    frame,
                    f"Name: {person_name}",
                    (
                        left,
                        max(55, top - 15)
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )


                # ==================================
                # SAMPLE COUNT
                # ==================================

                cv2.putText(
                    frame,
                    f"Samples: {sample_count}/{MAX_SAMPLES}",
                    (
                        left,
                        bottom + 30
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )


    # ==========================================
    # SHOW CAMERA
    # ==========================================

    cv2.imshow(
        "Face Enrollment",
        frame
    )


    # ESC
    if cv2.waitKey(1) & 0xFF == 27:

        break


    # ==========================================
    # 30 SAMPLES COMPLETED
    # ==========================================

    if sample_count >= MAX_SAMPLES:

        break


# ==========================================
# RELEASE CAMERA
# ==========================================

camera.release()

cv2.destroyAllWindows()


# ==========================================
# CHECK ENCODINGS
# ==========================================

if len(encodings) == 0:

    print("\nNo face encoding captured.")
    print("Enrollment failed.")

    exit()


# ==========================================
# SAVE DATA
# ==========================================

data = {
    "id": person_id,
    "name": person_name,
    "encodings": encodings
}


with open(
    file_path,
    "wb"
) as file:

    pickle.dump(
        data,
        file
    )


# ==========================================
# SUCCESS
# ==========================================

print("\n================================")
print("ENROLLMENT COMPLETED")
print("================================")

print("ID:", person_id)

print("Name:", person_name)

print(
    "Encodings saved:",
    len(encodings)
)

print(
    "Saved file:",
    file_path
)

print("================================")