import cv2
import sqlite3
import os
import numpy as np


# =========================================================
# CONFIGURATION
# =========================================================

YUNET_MODEL = os.path.join(
    "models",
    "face_detection_yunet_2026may.onnx"
)

SFACE_MODEL = os.path.join(
    "models",
    "face_recognition_sface_2021dec.onnx"
)

COSINE_THRESHOLD = 0.363


# =========================================================
# LOAD MODELS
# =========================================================

_detector = None
_recognizer = None


def load_models():

    global _detector
    global _recognizer

    if _detector is None:

        _detector = cv2.FaceDetectorYN.create(
            YUNET_MODEL,
            "",
            (320, 320),
            0.9,
            0.3,
            5000
        )

    if _recognizer is None:

        _recognizer = cv2.FaceRecognizerSF.create(
            SFACE_MODEL,
            ""
        )

    return _detector, _recognizer


# =========================================================
# GET STORED FACE
# =========================================================

def get_stored_face(student_id):

    conn = sqlite3.connect("students.db")

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT face_embedding
            FROM face_profiles
            WHERE student_id = ?
            """,
            (student_id,)
        )

        record = cursor.fetchone()

        if record is None:
            return None

        embedding = np.frombuffer(
            record[0],
            dtype=np.float32
        ).reshape(1, -1)

        return embedding

    finally:

        conn.close()


# =========================================================
# VERIFY FACE
# =========================================================

def verify_face(student_id):

    detector, recognizer = load_models()

    stored_embedding = get_stored_face(student_id)

    if stored_embedding is None:

        return False, 0.0, "Face not registered"


    camera = cv2.VideoCapture(0)

    if not camera.isOpened():

        return False, 0.0, "Camera could not be opened"


    try:

        while True:

            success, frame = camera.read()

            if not success:

                return False, 0.0, "Could not read camera"


            height, width = frame.shape[:2]

            detector.setInputSize(
                (width, height)
            )

            _, faces = detector.detect(frame)

            face_count = 0

            if faces is not None:

                face_count = len(faces)


            # ---------------------------------------------
            # STATUS
            # ---------------------------------------------

            if face_count == 1:

                status = "ONE FACE - READY"

            elif face_count == 0:

                status = "NO FACE"

            else:

                status = "MULTIPLE FACES"


            cv2.putText(
                frame,
                status,
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 255, 0),
                2
            )


            cv2.putText(
                frame,
                "Press SPACE to verify | Q to cancel",
                (20, 75),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2
            )


            cv2.imshow(
                "SAMS - Face Verification",
                frame
            )


            key = cv2.waitKey(1) & 0xFF


            # ---------------------------------------------
            # VERIFY
            # ---------------------------------------------

            if key == ord(" "):

                if face_count != 1:

                    continue


                face = faces[0]


                # Align face
                aligned_face = recognizer.alignCrop(
                    frame,
                    face
                )


                # Extract live feature
                live_feature = recognizer.feature(
                    aligned_face
                )


                if live_feature is None:

                    return (
                        False,
                        0.0,
                        "Could not extract face feature"
                    )


                # Compare
                similarity = recognizer.match(
                    stored_embedding,
                    live_feature,
                    cv2.FaceRecognizerSF_FR_COSINE
                )


                similarity = float(similarity)


                if similarity >= COSINE_THRESHOLD:

                    return (
                        True,
                        similarity,
                        "Face matched"
                    )


                return (
                    False,
                    similarity,
                    "Face not matched"
                )


            # ---------------------------------------------
            # CANCEL
            # ---------------------------------------------

            if key == ord("q"):

                return (
                    False,
                    0.0,
                    "Verification cancelled"
                )

    finally:

        camera.release()
        cv2.destroyAllWindows()