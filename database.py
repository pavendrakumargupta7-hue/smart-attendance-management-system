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

    # Enable foreign key support
    conn.execute("PRAGMA foreign_keys = ON")

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
        # STUDENTS TABLE MIGRATION
        # =================================================

        cursor.execute("PRAGMA table_info(students)")

        student_columns = [
            column["name"]
            for column in cursor.fetchall()
        ]

        # -------------------------------------------------
        # Add student_id if old database does not have it
        # -------------------------------------------------

        if "student_id" not in student_columns:

            cursor.execute("""
                ALTER TABLE students
                ADD COLUMN student_id TEXT
            """)

        # -------------------------------------------------
        # Add course
        # -------------------------------------------------

        if "course" not in student_columns:

            cursor.execute("""
                ALTER TABLE students
                ADD COLUMN course TEXT
            """)

        # -------------------------------------------------
        # Add semester
        # -------------------------------------------------

        if "semester" not in student_columns:

            cursor.execute("""
                ALTER TABLE students
                ADD COLUMN semester TEXT
            """)

        # -------------------------------------------------
        # Add created_at
        # -------------------------------------------------

        if "created_at" not in student_columns:

            cursor.execute("""
                ALTER TABLE students
                ADD COLUMN created_at TIMESTAMP
            """)

        # =================================================
        # FIX OLD STUDENT RECORDS
        # =================================================
        #
        # IMPORTANT:
        #
        # Existing attendance / face records may already
        # contain the internal student database ID.
        #
        # Therefore we use the existing students.id as the
        # legacy student_id instead of randomly generating
        # a new ID.
        #
        # Example:
        #
        # id = 3
        # student_id = "3"
        #
        # This prevents existing attendance references
        # from becoming disconnected.
        #
        # =================================================

        cursor.execute("""
            SELECT id
            FROM students
            WHERE student_id IS NULL
               OR TRIM(student_id) = ''
        """)

        students_without_id = cursor.fetchall()

        for student in students_without_id:

            student_db_id = student["id"]

            cursor.execute("""
                UPDATE students
                SET student_id = ?
                WHERE id = ?
            """, (
                str(student_db_id),
                student_db_id
            ))

        # =================================================
        # FIX OLD REGISTERED DATE
        # =================================================

        cursor.execute("""
            UPDATE students
            SET created_at = CURRENT_TIMESTAMP
            WHERE created_at IS NULL
               OR TRIM(created_at) = ''
        """)

        conn.commit()


        # =================================================
        # ADMINS TABLE
        # =================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                admin_id TEXT UNIQUE NOT NULL,

                name TEXT NOT NULL,

                email TEXT UNIQUE NOT NULL,

                password TEXT NOT NULL,

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
        # TEACHER-STUDENT ASSIGNMENT TABLE
        # =================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teacher_student (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                teacher_id INTEGER NOT NULL,

                student_id INTEGER NOT NULL,

                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(teacher_id, student_id),

                FOREIGN KEY(teacher_id)
                REFERENCES teachers(id)
                ON DELETE CASCADE,

                FOREIGN KEY(student_id)
                REFERENCES students(id)
                ON DELETE CASCADE
            )
        """)


        # =================================================
        # ATTENDANCE TABLE
        # =================================================
        #
        # Existing SAMS attendance flow uses the student's
        # database ID in attendance.student_id.
        #
        # Therefore this is kept compatible with the
        # existing application.
        #
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

                UNIQUE(student_id, date)
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

                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

                is_closed INTEGER NOT NULL DEFAULT 0,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(year, month)
            )
        """)

        # =================================================
        # ADD CLASS CLOSED COLUMN IF NOT EXISTS
        # =================================================

        try:

            cursor.execute(
                """
                ALTER TABLE class_schedule
                ADD COLUMN is_closed
                INTEGER NOT NULL DEFAULT 0
                """
            )

        except sqlite3.OperationalError:

            pass

        # =================================================
        # FINAL COMMIT
        # =================================================

        conn.commit()


    except Exception:

        conn.rollback()

        raise


    finally:

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
            (
                year,
                month
            )
        )

        record = cursor.fetchone()

        if record:

            return int(record["total_classes"])

        return DEFAULT_TOTAL_CLASSES

    finally:

        conn.close()
# =========================================================
# GET CLASS STATUS
# =========================================================

def get_class_status(year, month):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT is_closed
            FROM class_schedule
            WHERE year = ?
            AND month = ?
            """,
            (
                year,
                month
            )
        )

        record = cursor.fetchone()

        if record:

            return bool(record["is_closed"])

        return False

    finally:

        conn.close()


# =========================================================
# CLOSE CLASSES
# =========================================================

def close_classes(year, month):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE class_schedule
            SET is_closed = 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE year = ?
            AND month = ?
            """,
            (
                year,
                month
            )
        )

        conn.commit()

    finally:

        conn.close()

# =========================================================
# GET CLASS STATUS
# =========================================================

def get_class_status(year, month):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT is_closed
            FROM class_schedule
            WHERE year = ?
            AND month = ?
            """,
            (
                year,
                month
            )
        )

        record = cursor.fetchone()

        if record:

            return bool(record["is_closed"])

        return False

    finally:

        conn.close()


# =========================================================
# CLOSE CLASSES
# =========================================================

def close_classes(year, month):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE class_schedule
            SET is_closed = 1
            WHERE year = ?
            AND month = ?
            """,
            (
                year,
                month
            )
        )

        conn.commit()

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