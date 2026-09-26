import sqlite3
import os


# =========================================================
# DATABASE CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "students.db")

DEFAULT_TOTAL_CLASSES = 30


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# =========================================================
# CREATE DATABASE
# =========================================================

def create_database():

    conn = get_connection()
    cursor = conn.cursor()

    try:

        # =================================================
        # STUDENTS TABLE
        # =================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                password TEXT NOT NULL,
                course TEXT,
                semester TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # =================================================
        # TEACHERS TABLE
        # =================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teachers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # =================================================
        # ATTENDANCE TABLE
        # =================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                student_id TEXT NOT NULL,

                date TEXT NOT NULL,

                time TEXT NOT NULL,

                latitude REAL,

                longitude REAL,

                distance REAL,

                status TEXT DEFAULT 'Present',

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(student_id, date),

                FOREIGN KEY(student_id)
                REFERENCES students(student_id)
                ON DELETE CASCADE
            )
        """)
                # =================================================
        # FACE PROFILES TABLE
        # =================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS face_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                student_id TEXT UNIQUE NOT NULL,

                face_embedding BLOB NOT NULL,

                model_name TEXT NOT NULL,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(student_id)
                REFERENCES students(student_id)
                ON DELETE CASCADE
            )
        """)
        
        # =================================================
        # FACE PROFILES TABLE
        # =================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS face_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                student_id TEXT UNIQUE NOT NULL,

                face_embedding BLOB NOT NULL,

                model_name TEXT NOT NULL,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(student_id)
                REFERENCES students(student_id)
                ON DELETE CASCADE
            )
        """)

        # =================================================
        # CLASS SCHEDULE TABLE
        # =================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS class_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                year INTEGER NOT NULL,

                month INTEGER NOT NULL,

                total_classes INTEGER NOT NULL DEFAULT 30,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(year, month)
            )
        """)

        # =================================================
        # COMMIT
        # =================================================

        conn.commit()

    except Exception:

        conn.rollback()
        raise

    finally:

        # Connection is closed ONLY after
        # all database operations are completed.
        conn.close()


# =========================================================
# GET TOTAL CLASSES
# =========================================================

def get_total_classes(year, month):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT total_classes
            FROM class_schedule
            WHERE year = ?
            AND month = ?
            """,
            (year, month)
        )

        record = cursor.fetchone()

        if record:

            return int(record["total_classes"])

        return DEFAULT_TOTAL_CLASSES

    finally:

        conn.close()


# =========================================================
# SAVE / UPDATE TOTAL CLASSES
# =========================================================

def save_total_classes(year, month, total_classes):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO class_schedule
            (
                year,
                month,
                total_classes
            )
            VALUES (?, ?, ?)

            ON CONFLICT(year, month)
            DO UPDATE SET
                total_classes = excluded.total_classes,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                year,
                month,
                int(total_classes)
            )
        )

        conn.commit()

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


# =========================================================
# CREATE DATABASE WHEN MODULE LOADS
# =========================================================

create_database()