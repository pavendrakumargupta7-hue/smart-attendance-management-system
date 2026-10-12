import sqlite3
import hashlib
import streamlit as st
from database import get_connection


# =========================================================
# TEACHER DATABASE CONFIGURATION
# =========================================================

MAX_TEACHERS = 10


# =========================================================
# PASSWORD HASH
# =========================================================

def hash_password(password):

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# =========================================================
# CREATE / VERIFY TEACHER TABLE
# =========================================================

def create_teacher_table():

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS teachers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                teacher_id TEXT UNIQUE NOT NULL,

                name TEXT NOT NULL,

                email TEXT UNIQUE,

                password TEXT NOT NULL,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.commit()

    finally:

        conn.close()


# =========================================================
# GET TOTAL TEACHERS
# =========================================================

def get_total_teachers():

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM teachers
            """
        )

        result = cursor.fetchone()

        return int(result[0])

    finally:

        conn.close()


# =========================================================
# CHECK TEACHER LIMIT
# =========================================================

def can_create_teacher():

    total_teachers = get_total_teachers()

    return total_teachers < MAX_TEACHERS


# =========================================================
# GENERATE TEACHER ID
# =========================================================

def generate_teacher_id():

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT teacher_id
            FROM teachers
            ORDER BY id
            """
        )

        existing_ids = {
            row[0]
            for row in cursor.fetchall()
        }

        for number in range(
            1,
            MAX_TEACHERS + 1
        ):

            teacher_id = f"TCH{number:04d}"

            if teacher_id not in existing_ids:

                return teacher_id

        return None

    finally:

        conn.close()


# =========================================================
# CREATE TEACHER
# =========================================================

def create_teacher(
    name,
    email,
    password
):

    # -----------------------------------------------------
    # CHECK MAXIMUM TEACHERS
    # -----------------------------------------------------

    if not can_create_teacher():

        return {
            "success": False,
            "message": (
                "Maximum 10 teachers are allowed."
            ),
            "teacher_id": None
        }


    # -----------------------------------------------------
    # VALIDATE DATA
    # -----------------------------------------------------

    name = str(name).strip()
    email = str(email).strip().lower()
    password = str(password)


    if not name:

        return {
            "success": False,
            "message": "Teacher name is required.",
            "teacher_id": None
        }


    if not email:

        return {
            "success": False,
            "message": "Teacher email is required.",
            "teacher_id": None
        }


    if not password:

        return {
            "success": False,
            "message": "Teacher password is required.",
            "teacher_id": None
        }


    # -----------------------------------------------------
    # GENERATE TEACHER ID
    # -----------------------------------------------------

    teacher_id = generate_teacher_id()

    if teacher_id is None:

        return {
            "success": False,
            "message": (
                "No teacher ID is available."
            ),
            "teacher_id": None
        }


    # -----------------------------------------------------
    # SAVE TEACHER
    # -----------------------------------------------------

    conn = get_connection()

    try:

        cursor = conn.cursor()

        # ---------------------------------------------
        # CHECK DUPLICATE EMAIL
        # ---------------------------------------------

        cursor.execute(
            """
            SELECT id
            FROM teachers
            WHERE LOWER(email) = ?
            """,
            (email,)
        )

        existing_teacher = cursor.fetchone()

        if existing_teacher:

            return {
                "success": False,
                "message": (
                    "Teacher email already exists."
                ),
                "teacher_id": None
            }


        # ---------------------------------------------
        # HASH PASSWORD
        # ---------------------------------------------

        password_hash = hash_password(
            password
        )


        # ---------------------------------------------
        # INSERT TEACHER
        # ---------------------------------------------

        cursor.execute(
            """
            INSERT INTO teachers
            (
                teacher_id,
                name,
                email,
                password
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                teacher_id,
                name,
                email,
                password_hash
            )
        )

        conn.commit()


        return {
            "success": True,
            "message": (
                "Teacher created successfully."
            ),
            "teacher_id": teacher_id
        }


    except sqlite3.IntegrityError as e:

        conn.rollback()

        return {
            "success": False,
            "message": (
                f"Teacher could not be created: {e}"
            ),
            "teacher_id": None
        }


    except sqlite3.Error as e:

        conn.rollback()

        return {
            "success": False,
            "message": (
                f"Database error: {e}"
            ),
            "teacher_id": None
        }


    finally:

        conn.close()


# =========================================================
# TEACHER LOGIN
# =========================================================

def verify_teacher_login(
    email,
    password
):

    email = str(email).strip().lower()
    password_hash = hash_password(
        str(password)
    )

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                teacher_id,
                name,
                email
            FROM teachers
            WHERE LOWER(email) = ?
            AND password = ?
            """,
            (
                email,
                password_hash
            )
        )

        teacher = cursor.fetchone()

        if teacher is None:

            return None

        return {
            "id": teacher["id"],
            "teacher_id": teacher["teacher_id"],
            "name": teacher["name"],
            "email": teacher["email"]
        }

    finally:

        conn.close()


# =========================================================
# GET TEACHER BY ID
# =========================================================

def get_teacher_by_id(
    teacher_db_id
):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                teacher_id,
                name,
                email,
                created_at
            FROM teachers
            WHERE id = ?
            """,
            (teacher_db_id,)
        )

        teacher = cursor.fetchone()

        if teacher is None:

            return None

        return dict(teacher)

    finally:

        conn.close()


# =========================================================
# GET ALL TEACHERS
# =========================================================

def get_all_teachers():

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                teacher_id,
                name,
                email,
                created_at
            FROM teachers
            ORDER BY id
            """
        )

        teachers = cursor.fetchall()

        return [
            dict(teacher)
            for teacher in teachers
        ]

    finally:

        conn.close()


# =========================================================
# DELETE TEACHER
# =========================================================

def delete_teacher(
    teacher_db_id
):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM teachers
            WHERE id = ?
            """,
            (teacher_db_id,)
        )

        deleted = cursor.rowcount

        conn.commit()

        return deleted > 0

    except sqlite3.Error:

        conn.rollback()

        return False

    finally:

        conn.close()


# =========================================================
# GET STUDENTS ASSIGNED TO TEACHER
# =========================================================

def get_teacher_students(
    teacher_db_id
):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                s.id,
                s.student_id,
                s.name,
                s.email,
                s.course,
                s.semester,
                s.created_at
            FROM students s

            INNER JOIN teacher_student ts
                ON ts.student_id = s.id

            WHERE ts.teacher_id = ?

            ORDER BY s.name
            """,
            (teacher_db_id,)
        )

        students = cursor.fetchall()

        return [
            dict(student)
            for student in students
        ]

    finally:

        conn.close()


# =========================================================
# ASSIGN STUDENT TO TEACHER
# =========================================================

def assign_student_to_teacher(
    teacher_db_id,
    student_db_id
):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR IGNORE INTO teacher_student
            (
                teacher_id,
                student_id
            )
            VALUES (?, ?)
            """,
            (
                teacher_db_id,
                student_db_id
            )
        )

        conn.commit()

        return cursor.rowcount > 0

    except sqlite3.Error:

        conn.rollback()

        return False

    finally:

        conn.close()


# =========================================================
# REMOVE STUDENT FROM TEACHER
# =========================================================

def remove_student_from_teacher(
    teacher_db_id,
    student_db_id
):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM teacher_student
            WHERE teacher_id = ?
            AND student_id = ?
            """,
            (
                teacher_db_id,
                student_db_id
            )
        )

        deleted = cursor.rowcount

        conn.commit()

        return deleted > 0

    except sqlite3.Error:

        conn.rollback()

        return False

    finally:

        conn.close()


# =========================================================
# GET TEACHER COUNT
# =========================================================

def get_teacher_limit_status():

    total = get_total_teachers()

    return {
        "total": total,
        "maximum": MAX_TEACHERS,
        "remaining": max(
            0,
            MAX_TEACHERS - total
        ),
        "can_create": total < MAX_TEACHERS
    }


# =========================================================
# INITIALIZE MODULE
# =========================================================

create_teacher_table()