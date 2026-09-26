import cv2
import sqlite3
import os
import numpy as np


# =========================================================
# CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

YUNET_MODEL = os.path.join(
    BASE_DIR,
    "models",
    "face_detection_yunet_2026may.onnx"
)

SFACE_MODEL = os.path.join(
    BASE_DIR,
    "models",
    "face_recognition_sface_2021dec.onnx"
)


# =========================================================
# DATABASE
# =========================================================

DB_NAME = os.path.join(
    BASE_DIR,
    "students.db"
)


def get_connection():

    conn = sqlite3.connect(DB_NAME)

    return conn


# =========================================================
# LOAD MODELS
# =========================================================

_detector = None
_recognizer = None


def load_models():

    global _detector
    global _recognizer

    # -----------------------------------------------------
    # YuNet Face Detector
    # -----------------------------------------------------

    if _detector is None:

        if not os.path.exists(YUNET_MODEL):

            raise FileNotFoundError(
                f"YuNet model not found:\n{YUNET_MODEL}"
            )

        _detector = cv2.FaceDetectorYN.create(
            YUNET_MODEL,
            "",
            (320, 320),
            0.9,
            0.3,
            5000
        )

    # -----------------------------------------------------
    # SFace Face Recognizer
    # -----------------------------------------------------

    if _recognizer is None:

        if not os.path.exists(SFACE_MODEL):

            raise FileNotFoundError(
                f"SFace model not found:\n{SFACE_MODEL}"
            )

        _recognizer = cv2.FaceRecognizerSF.create(
            SFACE_MODEL,
            ""
        )

    return _detector, _recognizer


# =========================================================
# CREATE FACE EMBEDDING
# =========================================================

def create_face_embedding(image_bytes):

    try:

        detector, recognizer = load_models()

        # -------------------------------------------------
        # Convert image bytes → numpy array
        # -------------------------------------------------

        image_array = np.frombuffer(
            image_bytes,
            dtype=np.uint8
        )

        # -------------------------------------------------
        # Decode image
        # -------------------------------------------------

        frame = cv2.imdecode(
            image_array,
            cv2.IMREAD_COLOR
        )

        if frame is None:

            return None, "Unable to read captured image."

        # -------------------------------------------------
        # Get image dimensions
        # -------------------------------------------------

        height, width = frame.shape[:2]

        detector.setInputSize(
            (width, height)
        )

        # -------------------------------------------------
        # Detect faces
        # -------------------------------------------------

        _, faces = detector.detect(frame)

        # -------------------------------------------------
        # No face
        # -------------------------------------------------

        if faces is None or len(faces) == 0:

            return None, "No face detected."

        # -------------------------------------------------
        # Multiple faces
        # -------------------------------------------------

        if len(faces) > 1:

            return (
                None,
                "Multiple faces detected. "
                "Please capture only one student."
            )

        # -------------------------------------------------
        # One face
        # -------------------------------------------------

        face = faces[0]

        # -------------------------------------------------
        # Align face
        # -------------------------------------------------

        aligned_face = recognizer.alignCrop(
            frame,
            face
        )

        if aligned_face is None:

            return None, "Could not align face."

        # -------------------------------------------------
        # Generate SFace feature
        # -------------------------------------------------

        embedding = recognizer.feature(
            aligned_face
        )

        if embedding is None:

            return None, "Could not generate face embedding."

        # -------------------------------------------------
        # IMPORTANT:
        # SFace feature must be stored as float32
        # -------------------------------------------------

        embedding = np.asarray(
            embedding,
            dtype=np.float32
        )

        return (
            embedding,
            "Face embedding created successfully."
        )

    except Exception as e:

        return (
            None,
            f"Face processing error: {e}"
        )


# =========================================================
# SAVE FACE EMBEDDING
# =========================================================

def save_face_embedding(
    student_id,
    embedding,
    model_name="opencv_sface"
):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        # -------------------------------------------------
        # Make sure embedding is float32
        # -------------------------------------------------

        embedding = np.asarray(
            embedding,
            dtype=np.float32
        )

        # -------------------------------------------------
        # Convert embedding → bytes
        # -------------------------------------------------

        embedding_bytes = embedding.tobytes()

        # -------------------------------------------------
        # Insert / Update
        # -------------------------------------------------

        cursor.execute(
            """
            INSERT INTO face_profiles
            (
                student_id,
                face_embedding,
                model_name
            )
            VALUES (?, ?, ?)

            ON CONFLICT(student_id)
            DO UPDATE SET
                face_embedding = excluded.face_embedding,
                model_name = excluded.model_name,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                str(student_id),
                embedding_bytes,
                model_name
            )
        )

        conn.commit()

        return (
            True,
            "Face registered successfully."
        )

    except Exception as e:

        conn.rollback()

        return (
            False,
            f"Database error: {e}"
        )

    finally:

        conn.close()