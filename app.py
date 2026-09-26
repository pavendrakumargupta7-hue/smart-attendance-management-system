# Run by PowerShell:
                # cd "D:\Pavendra\Hello Journey\My Projects\Smart Attendance Management System (SAMS) 31 JULY 26\attendance_system"
                # py -m py_compile app.py
                # py -m streamlit run app.py


import streamlit as st
import sqlite3
import os
import pandas as pd

from io import BytesIO

import calendar

from datetime import datetime

from math import radians, sin, cos, sqrt, atan2

from database import (
    create_database,
    get_connection,
    get_total_classes,
    DEFAULT_TOTAL_CLASSES
)

from streamlit_geolocation import streamlit_geolocation

from face_service import (
    create_face_embedding,
    save_face_embedding
)

from face_recognition import verify_face

# =========================================================
# DATABASE
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "students.db")

create_database()

def get_connection():
    """Create a new database connection."""
    return sqlite3.connect(DB_NAME)

# =========================================================
# GET TOTAL CLASSES FOR A MONTH
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
            return record[0]

        return DEFAULT_TOTAL_CLASSES

    finally:

        conn.close()

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Smart Attendance Management System",
    page_icon="📚",
    layout="wide"
)

# =========================================================
# CONSTANTS
# =========================================================

COLLEGE_LATITUDE = 22.588810035671806
COLLEGE_LONGITUDE = 75.7809312737432

ALLOWED_RADIUS = 150  # meters

DEFAULT_TOTAL_CLASSES = 30

# =========================================================
# SESSION STATE
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "user_name" not in st.session_state:
    st.session_state.user_name = ""

if "teacher_logged_in" not in st.session_state:
    st.session_state.teacher_logged_in = False

if "teacher_id" not in st.session_state:
    st.session_state.teacher_id = None

if "teacher_name" not in st.session_state:
    st.session_state.teacher_name = ""

# =========================================================
# DISTANCE CALCULATION
# =========================================================

def calculate_distance(lat1, lon1, lat2, lon2):

    R = 6371000  # Earth radius in meters

    lat1 = radians(lat1)
    lon1 = radians(lon1)

    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c

# =========================================================
# APPLICATION TITLE
# =========================================================

st.title("Smart Attendance Management System")

# =========================================================
# LOGGED-IN STUDENT
# =========================================================

if st.session_state.logged_in:

    # =====================================================
    # STUDENT HEADER
    # =====================================================

    st.success(
        f"Welcome {st.session_state.user_name}"
    )

    st.subheader("Student Dashboard")

    # =====================================================
    # STUDENT SIDEBAR
    # =====================================================

    st.sidebar.success(
        f"Student: {st.session_state.user_name}"
    )

    student_menu = st.sidebar.selectbox(
        "Student Menu",
        [
            "Dashboard",
            "Attendance History"
        ],
        key="student_menu"
    )

    # =====================================================
    # STUDENT DASHBOARD
    # =====================================================

    if student_menu == "Dashboard":

        st.write("---")
        st.subheader("📍 Location Verification")

        location = streamlit_geolocation()

        if location:

            latitude = location.get("latitude")
            longitude = location.get("longitude")
            accuracy = location.get("accuracy")

            if latitude is not None and longitude is not None:

                st.session_state.latitude = latitude
                st.session_state.longitude = longitude
                st.session_state.accuracy = accuracy

                st.success(
                    "Location detected successfully!"
                )

                # =================================================
                # LOCATION DETAILS
                # =================================================

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.metric(
                        "Latitude",
                        f"{latitude:.6f}"
                    )

                with col2:

                    st.metric(
                        "Longitude",
                        f"{longitude:.6f}"
                    )

                with col3:

                    if accuracy is not None:

                        st.metric(
                            "GPS Accuracy",
                            f"{accuracy:.2f} m"
                        )

                    else:

                        st.metric(
                            "GPS Accuracy",
                            "N/A"
                        )

                # =================================================
                # DISTANCE
                # =================================================

                distance = calculate_distance(
                    latitude,
                    longitude,
                    COLLEGE_LATITUDE,
                    COLLEGE_LONGITUDE
                )

                st.session_state.distance = distance

                st.write(
                    f"**Distance from College:** "
                    f"{distance:.2f} meters"
                )

                # =================================================
                # LOCATION VERIFICATION
                # =================================================

                if distance <= ALLOWED_RADIUS:

                    st.success(
                        "✅ You are inside the attendance area."
                    )

                else:

                    st.error(
                        "❌ You are outside the attendance area."
                    )

                # =================================================
                # MARK ATTENDANCE
                # =================================================

                st.write("---")
                st.subheader("📝 Mark Attendance")

                if distance <= ALLOWED_RADIUS:

                    if st.button(
                        "Mark Attendance",
                        type="primary",
                        key="mark_attendance_button"
                    ):

                        # =====================================================
                        # STEP 1 — CHECK FACE REGISTRATION
                        # =====================================================

                        face_conn = get_connection()

                        try:

                            face_cursor = face_conn.cursor()

                            face_cursor.execute(
                                """
                                SELECT id
                                FROM face_profiles
                                WHERE student_id = ?
                                """,
                                (st.session_state.user_id,)
                            )

                            face_profile = face_cursor.fetchone()

                        except sqlite3.Error as e:

                            st.error(
                                f"❌ Face profile database error: {e}"
                            )

                            face_profile = None

                        finally:

                            face_conn.close()


                        # =====================================================
                        # NO FACE REGISTERED
                        # =====================================================

                        if face_profile is None:

                            st.warning(
                                "⚠️ Your face is not registered."
                            )

                            st.info(
                                "Please contact the teacher to register your face "
                                "before marking attendance."
                            )


                        # =====================================================
                        # FACE REGISTERED
                        # =====================================================

                        else:

                            st.info(
                                "📷 Face verification required."
                            )

                            st.write(
                                "Look directly at the camera and press SPACE "
                                "when ONE FACE - READY is displayed."
                            )


                            # =================================================
                            # FACE VERIFICATION
                            # =================================================

                            face_matched, similarity, message = verify_face(
                                st.session_state.user_id
                            )


                            # =================================================
                            # FACE NOT MATCHED
                            # =================================================

                            if not face_matched:

                                st.error(
                                    "❌ Face verification failed."
                                )

                                st.warning(
                                    f"Reason: {message}"
                                )

                                if similarity > 0:

                                    st.info(
                                        f"Face similarity: {similarity:.4f}"
                                    )

                                st.error(
                                    "🚫 Attendance has NOT been marked."
                                )


                            # =================================================
                            # FACE MATCHED
                            # =================================================

                            else:

                                st.success(
                                    "✅ Face verification successful."
                                )

                                st.info(
                                    f"Face similarity: {similarity:.4f}"
                                )


                                # =============================================
                                # ATTENDANCE DATE & TIME
                                # =============================================

                                current_date = datetime.now().strftime(
                                    "%Y-%m-%d"
                                )

                                current_time = datetime.now().strftime(
                                    "%H:%M:%S"
                                )


                                # =============================================
                                # SAVE ATTENDANCE
                                # =============================================

                                conn = get_connection()

                                try:

                                    cursor = conn.cursor()


                                    # -----------------------------------------
                                    # CHECK DUPLICATE ATTENDANCE
                                    # -----------------------------------------

                                    cursor.execute(
                                        """
                                        SELECT id
                                        FROM attendance
                                        WHERE student_id = ?
                                        AND date = ?
                                        """,
                                        (
                                            st.session_state.user_id,
                                            current_date
                                        )
                                    )

                                    record = cursor.fetchone()


                                    if record:

                                        st.warning(
                                            "⚠️ Attendance already marked today!"
                                        )


                                    else:

                                        # -------------------------------------
                                        # INSERT ATTENDANCE
                                        # -------------------------------------

                                        cursor.execute(
                                            """
                                            INSERT INTO attendance
                                            (
                                                student_id,
                                                date,
                                                time,
                                                status,
                                                latitude,
                                                longitude,
                                                distance
                                            )
                                            VALUES (?, ?, ?, ?, ?, ?, ?)
                                            """,
                                            (
                                                st.session_state.user_id,
                                                current_date,
                                                current_time,
                                                "Present",
                                                latitude,
                                                longitude,
                                                distance
                                            )
                                        )

                                        conn.commit()


                                        # -------------------------------------
                                        # SUCCESS
                                        # -------------------------------------

                                        st.success(
                                            "✅ Attendance Marked Successfully!"
                                        )

                                        st.info(
                                            f"Time: {current_time}"
                                        )

                                        st.info(
                                            f"Distance: {distance:.2f} meters"
                                        )

                                        st.info(
                                            f"Face Similarity: {similarity:.4f}"
                                        )


                                except sqlite3.Error as e:

                                    conn.rollback()

                                    st.error(
                                        f"❌ Database Error: {e}"
                                    )

                                finally:

                                    conn.close()


                    else:

                        st.error(
                            f"❌ You are outside the attendance area. "
                            f"Distance: {distance:.2f} meters"
                        )

    # =====================================================
    # STUDENT ATTENDANCE HISTORY
    # =====================================================

    elif student_menu == "Attendance History":

        st.write("---")
        st.subheader("📋 My Attendance History")

        conn = get_connection()

        try:

            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    date,
                    time,
                    status,
                    latitude,
                    longitude,
                    distance
                FROM attendance
                WHERE student_id = ?
                ORDER BY id DESC
                """,
                (st.session_state.user_id,)
            )

            records = cursor.fetchall()

        except sqlite3.Error as e:

            st.error(
                f"❌ Database Error: {e}"
            )

            records = []

        finally:

            conn.close()

        if records:

            history_df = pd.DataFrame(
                records,
                columns=[
                    "Date",
                    "Time",
                    "Status",
                    "Latitude",
                    "Longitude",
                    "Distance (m)"
                ]
            )

            st.dataframe(
                history_df,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "No attendance records found."
            )

    # =====================================================
    # STUDENT LOGOUT
    # =====================================================

    st.write("---")

    if st.button(
        "🚪 Logout",
        key="student_logout"
    ):

        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.user_name = ""

        st.rerun()

# =========================================================
# NOT LOGGED IN AS STUDENT
# =========================================================

else:

    # =====================================================
    # MAIN MENU
    # =====================================================

    menu = [
        "Register",
        "Login",
        "Teacher Login",
        "Teacher Dashboard"
    ]


    # =====================================================
    # TEACHER ALREADY LOGGED IN
    # =====================================================

    if st.session_state.teacher_logged_in:

        st.sidebar.success(
            f"Teacher: {st.session_state.teacher_name.replace(' Teacher', '')} Sir"
        )
        
        choice = "Teacher Dashboard"

    else:

        choice = st.sidebar.selectbox(
            "Menu",
            menu,
            key="main_menu"
        )


    # =====================================================
    # STUDENT REGISTER
    # =====================================================

    if choice == "Register":

        st.subheader("👨‍🎓 Student Registration")

        name = st.text_input(
            "Name",
            key="register_name"
        )

        email = st.text_input(
            "Email",
            key="register_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="register_password"
        )

        if st.button(
            "Register",
            type="primary",
            key="register_button"
        ):

            if not name or not email or not password:

                st.warning(
                    "Please fill all fields."
                )

            else:

                conn = get_connection()

                try:

                    cursor = conn.cursor()

                    cursor.execute(
                        """
                        INSERT INTO students
                        (name, email, password)
                        VALUES (?, ?, ?)
                        """,
                        (
                            name.strip(),
                            email.strip().lower(),
                            password
                        )
                    )

                    conn.commit()

                    st.success(
                        "✅ Registration Successful!"
                    )

                except sqlite3.IntegrityError:

                    st.error(
                        "This email is already registered."
                    )

                except sqlite3.Error as e:

                    st.error(
                        f"❌ Database Error: {e}"
                    )

                finally:

                    conn.close()


    # =====================================================
    # STUDENT LOGIN
    # =====================================================

    elif choice == "Login":

        st.subheader("🔐 Student Login")

        email = st.text_input(
            "Email",
            key="login_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button(
            "Login",
            type="primary",
            key="login_button"
        ):

            conn = get_connection()

            try:

                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT id, name
                    FROM students
                    WHERE LOWER(TRIM(email)) = ?
                    AND password = ?
                    """,
                    (
                        email.strip().lower(),
                        password
                    )
                )

                user = cursor.fetchone()

            except sqlite3.Error as e:

                st.error(
                    f"❌ Database Error: {e}"
                )

                user = None

            finally:

                conn.close()

            if user:

                st.session_state.logged_in = True
                st.session_state.user_id = user[0]
                st.session_state.user_name = user[1]

                st.rerun()

            else:

                st.error(
                    "❌ Invalid Email or Password"
                )


    # =====================================================
    # TEACHER LOGIN
    # =====================================================

    elif choice == "Teacher Login":

        st.subheader("👨‍🏫 Teacher Login")

        teacher_email = st.text_input(
            "Teacher Email",
            key="teacher_login_email"
        )

        teacher_password = st.text_input(
            "Teacher Password",
            type="password",
            key="teacher_login_password"
        )

        if st.button(
            "Teacher Login",
            type="primary",
            key="teacher_login_button"
        ):

            if not teacher_email or not teacher_password:

                st.warning(
                    "Please enter email and password."
                )

            else:

                conn = get_connection()

                try:

                    cursor = conn.cursor()

                    cursor.execute(
                        """
                        SELECT id, name
                        FROM teachers
                        WHERE LOWER(TRIM(email)) = ?
                        AND password = ?
                        """,
                        (
                            teacher_email.strip().lower(),
                            teacher_password.strip()
                        )
                    )

                    teacher = cursor.fetchone()

                except sqlite3.Error as e:

                    st.error(
                        f"❌ Database Error: {e}"
                    )

                    teacher = None

                finally:

                    conn.close()

                if teacher:

                    st.session_state.teacher_logged_in = True
                    st.session_state.teacher_id = teacher[0]
                    st.session_state.teacher_name = teacher[1]

                    st.rerun()

                else:

                    st.error(
                        "❌ Invalid Teacher Email or Password"
                    )


    # =====================================================
    # TEACHER DASHBOARD
    # =====================================================

    elif choice == "Teacher Dashboard" and st.session_state.teacher_logged_in:

        # =================================================
        # TEACHER SIDEBAR
        # =================================================

        teacher_menu = st.sidebar.selectbox(
        "Teacher Menu",
        [
            "🏠 Dashboard",
            "👨‍🎓 Student Management",
            "📅 Attendance",
            "⚙️ Class Settings",
            "📊 Reports",
            "📈 Analytics",
            "📥 Export"
        ],
        key="teacher_menu"
        )


        # =================================================
        # TEACHER HEADER
        # =================================================

        st.subheader(
            f"👨‍🏫 Welcome {st.session_state.teacher_name.replace(' Teacher', '')} Sir"
        )

        st.write("---")


        # =================================================
        # DATABASE CONNECTION
        # =================================================

        conn = get_connection()

        try:

            cursor = conn.cursor()


            # =================================================
            # DASHBOARD
            # =================================================

            if teacher_menu == "🏠 Dashboard":

                st.subheader("🏠 Teacher Dashboard")


                # ---------------------------------------------
                # STATISTICS
                # ---------------------------------------------

                cursor.execute(
                    "SELECT COUNT(*) FROM students"
                )

                total_students = cursor.fetchone()[0]


                cursor.execute(
                    "SELECT COUNT(*) FROM attendance"
                )

                total_attendance = cursor.fetchone()[0]


                today = datetime.now().strftime(
                    "%Y-%m-%d"
                )

                # ---------------------------------------------
                # CURRENT MONTH CLASS SETTINGS
                # ---------------------------------------------

                current_date = datetime.now().date()

                current_year = current_date.year
                current_month = current_date.month

                current_month_classes = get_total_classes(
                    current_year,
                    current_month
                )

                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM attendance
                    WHERE date = ?
                    AND status = 'Present'
                    """,
                    (today,)
                )

                present_today = cursor.fetchone()[0]


                absent_today = max(
                    total_students - present_today,
                    0
                )


                if total_students > 0:

                    today_percentage = (
                        present_today /
                        total_students
                    ) * 100

                else:

                    today_percentage = 0


                # ---------------------------------------------
                # DISPLAY STATISTICS
                # ---------------------------------------------

                st.subheader(
                    "📊 Today's Statistics"
                )

                col1, col2, col3, col4, col5 = st.columns(5)

                with col1:

                    st.metric(
                        "Total Students",
                        total_students
                    )

                with col2:

                    st.metric(
                        "Present Today",
                        present_today
                    )

                with col3:

                    st.metric(
                        "Absent Today",
                        absent_today
                    )

                with col4:

                    st.metric(
                        "Attendance %",
                        f"{today_percentage:.2f}%"
                    )

                with col5:

                    st.metric(
                        "Current Month Classes",
                        current_month_classes
                    )

                st.write("---")

                st.metric(
                    "Total Attendance Records",
                    total_attendance
                )


                # ---------------------------------------------
                # TODAY'S ATTENDANCE
                # ---------------------------------------------

                st.write("---")

                st.subheader(
                    "📅 Today's Attendance"
                )

                cursor.execute(
                    """
                    SELECT
                        students.name,
                        attendance.time,
                        attendance.status,
                        attendance.distance
                    FROM attendance
                    JOIN students
                    ON students.id = attendance.student_id
                    WHERE attendance.date = ?
                    ORDER BY attendance.id DESC
                    """,
                    (today,)
                )

                today_records = cursor.fetchall()


                if today_records:

                    today_df = pd.DataFrame(
                        today_records,
                        columns=[
                            "Student Name",
                            "Time",
                            "Status",
                            "Distance (m)"
                        ]
                    )

                    st.dataframe(
                        today_df,
                        use_container_width=True,
                        hide_index=True
                    )

                else:

                    st.info(
                        "No attendance marked today."
                    )


            # =================================================
            # STUDENT MANAGEMENT
            # =================================================

            elif teacher_menu == "👨‍🎓 Student Management":

                st.subheader(
                    "👨‍🎓 Student Management"
                )


                # ---------------------------------------------
                # SEARCH STUDENT
                # ---------------------------------------------

                st.write("---")

                st.subheader(
                    "🔎 Search Student"
                )

                search_name = st.text_input(
                    "Enter Student Name",
                    key="teacher_search"
                )


                if search_name.strip():

                    cursor.execute(
                        """
                        SELECT
                            id,
                            name,
                            email
                        FROM students
                        WHERE LOWER(name) LIKE ?
                        ORDER BY name
                        """,
                        (
                            "%" +
                            search_name.strip().lower() +
                            "%",
                        )
                    )

                    search_students = cursor.fetchall()


                    if search_students:

                        search_df = pd.DataFrame(
                            search_students,
                            columns=[
                                "Student ID",
                                "Student Name",
                                "Email"
                            ]
                        )

                        st.dataframe(
                            search_df,
                            use_container_width=True,
                            hide_index=True
                        )

                    else:

                        st.warning(
                            "⚠️ No matching student found."
                        )


                # ---------------------------------------------
                # ALL STUDENTS
                # ---------------------------------------------

                st.write("---")

                st.subheader(
                    "👨‍🎓 All Registered Students"
                )

                cursor.execute(
                    """
                    SELECT
                        id,
                        name,
                        email
                    FROM students
                    ORDER BY name
                    """
                )

                students_list = cursor.fetchall()


                if students_list:

                    students_df = pd.DataFrame(
                        students_list,
                        columns=[
                            "Student ID",
                            "Student Name",
                            "Email"
                        ]
                    )

                    st.dataframe(
                        students_df,
                        use_container_width=True,
                        hide_index=True
                    )

                    st.success(
                        f"Total Registered Students: "
                        f"{len(students_list)}"
                    )

                    # =================================================
                    # EDIT STUDENT
                    # =================================================

                    st.write("---")
                    st.subheader("✏️ Edit Student")

                    if students_list:

                        student_options = {
                            f"{student[1]} ({student[2]})": student[0]
                            for student in students_list
                        }

                        selected_edit_student = st.selectbox(
                            "Select Student to Edit",
                            list(student_options.keys()),
                            key="edit_student_select"
                        )

                        selected_edit_student_id = student_options[
                            selected_edit_student
                        ]

                        # ---------------------------------------------
                        # Get selected student details
                        # ---------------------------------------------

                        cursor.execute(
                            """
                            SELECT name, email
                            FROM students
                            WHERE id = ?
                            """,
                            (selected_edit_student_id,)
                        )

                        edit_student = cursor.fetchone()

                        if edit_student:

                            current_name = edit_student[0]
                            current_email = edit_student[1]

                            new_name = st.text_input(
                                "Student Name",
                                value=current_name,
                                key="edit_student_name"
                            )

                            new_email = st.text_input(
                                "Student Email",
                                value=current_email,
                                key="edit_student_email"
                            )

                            # ---------------------------------------------
                            # UPDATE STUDENT
                            # ---------------------------------------------

                            if st.button(
                                "💾 Update Student",
                                type="primary",
                                key="update_student_button"
                            ):

                                new_name = new_name.strip()
                                new_email = new_email.strip()

                                if not new_name or not new_email:

                                    st.warning(
                                        "⚠️ Name and Email cannot be empty."
                                    )

                                else:

                                    try:

                                        cursor.execute(
                                            """
                                            UPDATE students
                                            SET name = ?,
                                                email = ?
                                            WHERE id = ?
                                            """,
                                            (
                                                new_name,
                                                new_email,
                                                selected_edit_student_id
                                            )
                                        )

                                        conn.commit()

                                        st.success(
                                            "✅ Student details updated successfully."
                                        )

                                        st.rerun()

                                    except sqlite3.IntegrityError:

                                        st.error(
                                            "❌ This email is already registered "
                                            "with another student."
                                        )

                                    except sqlite3.Error as e:

                                        conn.rollback()

                                        st.error(
                                            f"❌ Database Error: {e}"
                                        )

                    else:

                        st.info(
                            "No students available to edit."
                        )

                    # =================================================
                    # STUDENT PROFILE / VIEW DETAILS
                    # =================================================

                    st.write("---")
                    st.subheader("👤 Student Profile")

                    if students_list:

                        profile_options = {
                            f"{student[1]} ({student[2]})": student[0]
                            for student in students_list
                        }

                        selected_profile_student = st.selectbox(
                            "Select Student",
                            list(profile_options.keys()),
                            key="profile_student_select"
                        )

                        selected_profile_student_id = profile_options[
                            selected_profile_student
                        ]

                        # =================================================
                        # STUDENT BASIC DETAILS
                        # =================================================

                        cursor.execute(
                            """
                            SELECT
                                id,
                                name,
                                email
                            FROM students
                            WHERE id = ?
                            """,
                            (selected_profile_student_id,)
                        )

                        profile_student = cursor.fetchone()

                        if profile_student:

                            student_id = profile_student[0]
                            student_name = profile_student[1]
                            student_email = profile_student[2]

                            st.write("---")
                            st.subheader("📋 Student Information")

                            col1, col2, col3 = st.columns(3)

                            with col1:
                                st.metric(
                                    "Student ID",
                                    student_id
                                )

                            with col2:
                                st.metric(
                                    "Student Name",
                                    student_name
                                )

                            with col3:
                                st.metric(
                                    "Email",
                                    student_email
                                )

                            # =================================================
                            # ATTENDANCE STATISTICS
                            # =================================================

                            # -------------------------------------------------
                            # CURRENT MONTH / YEAR
                            # -------------------------------------------------

                            current_date = datetime.now()

                            current_year = current_date.year
                            current_month = current_date.month


                            # -------------------------------------------------
                            # CURRENT MONTH PRESENT ATTENDANCE
                            # -------------------------------------------------

                            cursor.execute(
                                """
                                SELECT COUNT(*)
                                FROM attendance
                                WHERE student_id = ?
                                AND strftime('%Y', date) = ?
                                AND strftime('%m', date) = ?
                                """,
                                (
                                    student_id,
                                    str(current_year),
                                    f"{current_month:02d}"
                                )
                            )

                            present_count = cursor.fetchone()[0]


                            # -------------------------------------------------
                            # GET TOTAL CLASSES FOR CURRENT MONTH
                            # -------------------------------------------------

                            monthly_classes = get_total_classes(
                                current_year,
                                current_month
                            )


                            # -------------------------------------------------
                            # ATTENDANCE PERCENTAGE
                            # -------------------------------------------------

                            if monthly_classes > 0:

                                attendance_percentage = (
                                    present_count / monthly_classes
                                ) * 100

                            else:

                                attendance_percentage = 0


                            # -------------------------------------------------
                            # ATTENDANCE STATISTICS UI
                            # -------------------------------------------------

                            st.write("---")
                            st.subheader("📊 Attendance Statistics")

                            col1, col2, col3 = st.columns(3)


                            with col1:

                                st.metric(
                                    "Present",
                                    present_count
                                )


                            with col2:

                                st.metric(
                                    "Total Classes",
                                    monthly_classes
                                )


                            with col3:

                                st.metric(
                                    "Attendance %",
                                    f"{attendance_percentage:.2f}%"
                                )


                            # =================================================
                            # ATTENDANCE HISTORY
                            # =================================================

                            st.write("---")
                            st.subheader("📅 Attendance History")

                            cursor.execute(
                                """
                                SELECT
                                    date,
                                    time,
                                    status,
                                    latitude,
                                    longitude,
                                    distance
                                FROM attendance
                                WHERE student_id = ?
                                ORDER BY id DESC
                                """,
                                (student_id,)
                            )

                            profile_attendance = cursor.fetchall()


                            if profile_attendance:

                                profile_df = pd.DataFrame(
                                    profile_attendance,
                                    columns=[
                                        "Date",
                                        "Time",
                                        "Status",
                                        "Latitude",
                                        "Longitude",
                                        "Distance (m)"
                                    ]
                                )

                                # -------------------------------------------------
                                # FORMAT LOCATION DATA
                                # -------------------------------------------------

                                profile_df["Latitude"] = profile_df["Latitude"].apply(
                                    lambda x: f"{x:.6f}" if pd.notna(x) else "-"
                                )

                                profile_df["Longitude"] = profile_df["Longitude"].apply(
                                    lambda x: f"{x:.6f}" if pd.notna(x) else "-"
                                )

                                profile_df["Distance (m)"] = profile_df["Distance (m)"].apply(
                                    lambda x: f"{x:.2f}" if pd.notna(x) else "-"
                                )

                                # -------------------------------------------------
                                # DISPLAY TABLE
                                # -------------------------------------------------

                                st.dataframe(
                                    profile_df,
                                    use_container_width=True,
                                    hide_index=True
                                )

                            else:

                                st.info(
                                    "No attendance records found for this student."
                                )
                                                    # =================================================
                    # FACE REGISTRATION
                    # =================================================

                    st.write("---")
                    st.subheader("📸 Register Student Face")

                    face_student_options = {
                        f"{student[1]} (ID: {student[0]})":
                        student[0]
                        for student in students_list
                    }

                    selected_face_student = st.selectbox(
                        "Select Student for Face Registration",
                        list(face_student_options.keys()),
                        key="register_face_student_select"
                    )

                    selected_face_student_id = face_student_options[
                        selected_face_student
                    ]

                    # -------------------------------------------------
                    # GET STUDENT NAME
                    # -------------------------------------------------

                    cursor.execute(
                        """
                        SELECT name
                        FROM students
                        WHERE id = ?
                        """,
                        (selected_face_student_id,)
                    )

                    face_student = cursor.fetchone()

                    if face_student:

                        face_student_name = face_student[0]

                        st.info(
                            f"Selected Student: "
                            f"**{face_student_name}** "
                            f"(ID: {selected_face_student_id})"
                        )

                        # -------------------------------------------------
                        # CHECK EXISTING FACE
                        # -------------------------------------------------

                        cursor.execute(
                            """
                            SELECT
                                id,
                                model_name,
                                created_at
                            FROM face_profiles
                            WHERE student_id = ?
                            """,
                            (selected_face_student_id,)
                        )

                        existing_face = cursor.fetchone()

                        if existing_face:

                            st.success(
                                "✅ Face is already registered "
                                "for this student."
                            )

                            st.caption(
                                f"Model: {existing_face[1]} | "
                                f"Registered: {existing_face[2]}"
                            )

                            st.warning(
                                "⚠️ Capturing a new face will "
                                "replace the existing face registration."
                            )

                        else:

                            st.warning(
                                "⚠️ Face is not registered "
                                "for this student."
                            )

                        # -------------------------------------------------
                        # OPEN CAMERA BUTTON
                        # -------------------------------------------------

                        if st.button(
                            "📸 Open Camera",
                            type="primary",
                            key="open_student_face_button"
                        ):
                            st.session_state["face_camera_open"] = True

                        # -------------------------------------------------
                        # CAMERA
                        # -------------------------------------------------

                        camera_image = None

                        if st.session_state.get("face_camera_open", False):

                            camera_image = st.camera_input(
                                "📷 Take Student Face Photo",
                                key="student_face_camera",
                                resolution="720p"
                            )

                        if camera_image:

                            st.image(
                                camera_image,
                                caption="Captured Student Face",
                                width=350
                            )

                            # -------------------------------------------------
                            # REGISTER BUTTON
                            # -------------------------------------------------

                            if st.button(
                                "💾 Register Face",
                                type="primary",
                                key="save_student_face_button"
                            ):

                                with st.spinner(
                                    "🔄 Detecting face and creating embedding..."
                                ):

                                    embedding, message = (
                                        create_face_embedding(
                                            camera_image.getvalue()
                                        )
                                    )

                                # -------------------------------------------------
                                # FACE PROCESSING FAILED
                                # -------------------------------------------------

                                if embedding is None:

                                    st.error(
                                        f"❌ {message}"
                                    )

                                # -------------------------------------------------
                                # FACE PROCESSING SUCCESS
                                # -------------------------------------------------

                                else:

                                    st.success(
                                        f"✅ {message}"
                                    )

                                    with st.spinner(
                                        "💾 Saving face registration..."
                                    ):

                                        success, save_message = (
                                            save_face_embedding(
                                                selected_face_student_id,
                                                embedding
                                            )
                                        )

                                    if success:

                                        st.success(
                                            f"✅ {save_message}"
                                        )

                                        st.info(
                                            f"Student: "
                                            f"{face_student_name} | "
                                            f"Student ID: "
                                            f"{selected_face_student_id}"
                                        )

                                        st.rerun()

                                    else:

                                        st.error(
                                            f"❌ {save_message}"
                                        )
                                        
                    # -----------------------------------------
                    # REMOVE STUDENT
                    # -----------------------------------------

                    st.write("---")

                    st.subheader(
                        "🗑️ Remove Student"
                    )

                    student_options = {
                        f"{student[1]} ({student[2]})":
                        student[0]
                        for student in students_list
                    }

                    selected_student = st.selectbox(
                        "Select Student",
                        list(student_options.keys()),
                        key="remove_student_select"
                    )

                    selected_student_id = student_options[
                        selected_student
                    ]

                    st.warning(
                        "⚠️ Removing a student will also "
                        "remove all attendance records "
                        "of that student."
                    )

                    confirm_delete = st.checkbox(
                        "I understand that this action cannot be undone.",
                        key="confirm_delete_student"
                    )

                    if st.button(
                        "🗑️ Remove Selected Student",
                        type="secondary",
                        key="remove_student_button"
                    ):

                        if not confirm_delete:

                            st.error(
                                "❌ Please confirm the deletion first."
                            )

                        else:

                            try:

                                # -----------------------------------------
                                # DELETE ATTENDANCE RECORDS
                                # -----------------------------------------

                                cursor.execute(
                                    """
                                    DELETE FROM attendance
                                    WHERE student_id = ?
                                    """,
                                    (selected_student_id,)
                                )

                                deleted_attendance = cursor.rowcount


                                # -----------------------------------------
                                # DELETE STUDENT
                                # -----------------------------------------

                                cursor.execute(
                                    """
                                    DELETE FROM students
                                    WHERE id = ?
                                    """,
                                    (selected_student_id,)
                                )

                                deleted_student = cursor.rowcount


                                # -----------------------------------------
                                # COMMIT TRANSACTION
                                # -----------------------------------------

                                conn.commit()


                                # -----------------------------------------
                                # VERIFY DELETION
                                # -----------------------------------------

                                cursor.execute(
                                    """
                                    SELECT COUNT(*)
                                    FROM students
                                    WHERE id = ?
                                    """,
                                    (selected_student_id,)
                                )

                                remaining_student = cursor.fetchone()[0]


                                cursor.execute(
                                    """
                                    SELECT COUNT(*)
                                    FROM attendance
                                    WHERE student_id = ?
                                    """,
                                    (selected_student_id,)
                                )

                                remaining_attendance = cursor.fetchone()[0]


                                # -----------------------------------------
                                # FINAL RESULT
                                # -----------------------------------------

                                if (
                                    deleted_student > 0
                                    and remaining_student == 0
                                    and remaining_attendance == 0
                                ):

                                    st.success(
                                        "✅ Student removed successfully."
                                    )

                                    st.info(
                                        f"Student ID: {selected_student_id} | "
                                        f"Attendance records removed: "
                                        f"{deleted_attendance}"
                                    )

                                    st.rerun()

                                else:

                                    st.error(
                                        "❌ Student deletion could not be verified."
                                    )

                            except sqlite3.Error as e:

                                conn.rollback()

                                st.error(
                                    f"❌ Database Error: {e}"
                                )

                                # =================================================
                                # EDIT STUDENT
                                # =================================================

                                st.write("---")
                                st.subheader("✏️ Edit Student")

                                if students_list:

                                    edit_student_options = {
                                        f"{student[1]} ({student[2]})": student[0]
                                        for student in students_list
                                    }

                                    selected_edit_student = st.selectbox(
                                        "Select Student to Edit",
                                        list(edit_student_options.keys()),
                                        key="edit_student_select"
                                    )

                                    selected_edit_student_id = edit_student_options[
                                        selected_edit_student
                                    ]

                                    # ---------------------------------------------
                                    # GET CURRENT STUDENT DATA
                                    # ---------------------------------------------

                                    cursor.execute(
                                        """
                                        SELECT name, email
                                        FROM students
                                        WHERE id = ?
                                        """,
                                        (selected_edit_student_id,)
                                    )

                                    current_student = cursor.fetchone()

                                    if current_student:

                                        current_name = current_student[0]
                                        current_email = current_student[1]

                                        # ---------------------------------------------
                                        # EDIT FORM
                                        # ---------------------------------------------

                                        with st.form(
                                            "edit_student_form"
                                        ):

                                            new_name = st.text_input(
                                                "Student Name",
                                                value=current_name,
                                                key="edit_student_name"
                                            )

                                            new_email = st.text_input(
                                                "Student Email",
                                                value=current_email,
                                                key="edit_student_email"
                                            )

                                            new_password = st.text_input(
                                                "New Password",
                                                type="password",
                                                key="edit_student_password"
                                            )

                                            update_student = st.form_submit_button(
                                                "💾 Update Student",
                                                type="primary"
                                            )

                                            if update_student:

                                                new_name = new_name.strip()
                                                new_email = new_email.strip()

                                                if not new_name or not new_email:

                                                    st.warning(
                                                        "⚠️ Name and Email cannot be empty."
                                                    )

                                                else:

                                                    try:

                                                        # ---------------------------------
                                                        # UPDATE NAME + EMAIL
                                                        # ---------------------------------

                                                        if new_password.strip():

                                                            cursor.execute(
                                                                """
                                                                UPDATE students
                                                                SET
                                                                    name = ?,
                                                                    email = ?,
                                                                    password = ?
                                                                WHERE id = ?
                                                                """,
                                                                (
                                                                    new_name,
                                                                    new_email,
                                                                    new_password.strip(),
                                                                    selected_edit_student_id
                                                                )
                                                            )

                                                        else:

                                                            cursor.execute(
                                                                """
                                                                UPDATE students
                                                                SET
                                                                    name = ?,
                                                                    email = ?
                                                                WHERE id = ?
                                                                """,
                                                                (
                                                                    new_name,
                                                                    new_email,
                                                                    selected_edit_student_id
                                                                )
                                                            )

                                                        conn.commit()

                                                        st.success(
                                                            "✅ Student details updated successfully."
                                                        )

                                                        st.rerun()

                                                    except sqlite3.IntegrityError:

                                                        conn.rollback()

                                                        st.error(
                                                            "❌ This email is already registered "
                                                            "with another student."
                                                        )

                                                    except sqlite3.Error as e:

                                                        conn.rollback()

                                                        st.error(
                                                            f"❌ Database Error: {e}"
                                                        )

                                else:

                                    st.info(
                                        "No students available to edit."
                                    )

                                st.rerun()


                            except sqlite3.Error as e:

                                conn.rollback()

                                st.error(
                                    f"❌ Database Error: {e}"
                                )


                else:

                    st.info(
                        "No students registered yet."
                    )


            # =================================================
            # ATTENDANCE
            # =================================================

            elif teacher_menu == "📅 Attendance":

                st.subheader(
                    "📅 Attendance Management"
                )


                # ---------------------------------------------
                # TODAY'S ATTENDANCE
                # ---------------------------------------------

                st.write("---")

                st.subheader(
                    "📅 Today's Attendance"
                )

                today = datetime.now().strftime(
                    "%Y-%m-%d"
                )
                cursor.execute(
                    """
                    SELECT
                        students.name,
                        attendance.date,
                        attendance.time,
                        attendance.status,
                        attendance.latitude,
                        attendance.longitude,
                        attendance.distance
                    FROM attendance
                    JOIN students
                    ON students.id =
                       attendance.student_id
                    WHERE attendance.date = ?
                    ORDER BY attendance.id DESC
                    """,
                    (today,)
                )

                today_records = cursor.fetchall()


                if today_records:

                    today_df = pd.DataFrame(
                        today_records,
                        columns=[
                            "Student Name",
                            "Date",
                            "Time",
                            "Status",
                            "Latitude",
                            "Longitude",
                            "Distance (m)"
                        ]
                    )

                    st.dataframe(
                        today_df,
                        use_container_width=True,
                        hide_index=True
                    )

                else:

                    st.info(
                        "No attendance marked today."
                    )


                # ---------------------------------------------
                # DATE-WISE ATTENDANCE
                # ---------------------------------------------

                st.write("---")

                st.subheader(
                    "📅 Date-wise Attendance"
                )


                selected_date = st.date_input(
                    "Select Attendance Date",
                    datetime.now().date(),
                    key="attendance_date"
                )


                selected_date_string = (
                    selected_date.strftime(
                        "%Y-%m-%d"
                    )
                )


                cursor.execute(
                    """
                    SELECT
                        students.name,
                        attendance.date,
                        attendance.time,
                        attendance.status,
                        attendance.latitude,
                        attendance.longitude,
                        attendance.distance
                    FROM attendance
                    JOIN students
                    ON students.id =
                       attendance.student_id
                    WHERE attendance.date = ?
                    ORDER BY attendance.id DESC
                    """,
                    (
                        selected_date_string,
                    )
                )

                date_records = cursor.fetchall()


                if date_records:

                    date_df = pd.DataFrame(
                        date_records,
                        columns=[
                            "Student Name",
                            "Date",
                            "Time",
                            "Status",
                            "Latitude",
                            "Longitude",
                            "Distance (m)"
                        ]
                    )

                    st.dataframe(
                        date_df,
                        use_container_width=True,
                        hide_index=True
                    )

                else:

                    st.info(
                        f"No attendance found for "
                        f"{selected_date_string}"
                    )

                # =================================================
                # ATTENDANCE FILTER
                # =================================================

                st.write("---")
                st.subheader("🔎 Filter Attendance")

                # =================================================
                # FILTER INPUTS
                # =================================================

                col1, col2, col3 = st.columns(3)

                with col1:

                    filter_student = st.text_input(
                        "Student Name",
                        key="filter_student_name"
                    )

                with col2:

                    filter_date = st.date_input(
                        "Attendance Date",
                        value=None,
                        key="filter_attendance_date"
                    )

                with col3:

                    filter_status = st.selectbox(
                        "Status",
                        [
                            "All",
                            "Present"
                        ],
                        key="filter_attendance_status"
                    )

                # =================================================
                # BUILD QUERY
                # =================================================

                query = """
                    SELECT
                        students.id,
                        students.name,
                        students.email,
                        attendance.date,
                        attendance.time,
                        attendance.status,
                        attendance.latitude,
                        attendance.longitude,
                        attendance.distance
                    FROM attendance
                    JOIN students
                    ON students.id = attendance.student_id
                    WHERE 1=1
                """

                query_params = []

                # =================================================
                # STUDENT FILTER
                # =================================================

                if filter_student.strip():

                    query += """
                        AND students.name LIKE ?
                    """

                    query_params.append(
                        "%" + filter_student.strip() + "%"
                    )

                # =================================================
                # DATE FILTER
                # =================================================

                if filter_date is not None:

                    filter_date_string = filter_date.strftime(
                        "%Y-%m-%d"
                    )

                    query += """
                        AND attendance.date = ?
                    """

                    query_params.append(
                        filter_date_string
                    )

                # =================================================
                # STATUS FILTER
                # =================================================

                if filter_status != "All":

                    query += """
                        AND attendance.status = ?
                    """

                    query_params.append(
                        filter_status
                    )

                # =================================================
                # ORDER
                # =================================================

                query += """
                    ORDER BY attendance.id DESC
                """

                # =================================================
                # EXECUTE QUERY
                # =================================================

                cursor.execute(
                    query,
                    query_params
                )

                filtered_records = cursor.fetchall()

                # =================================================
                # DISPLAY RESULT
                # =================================================

                if filtered_records:

                    filtered_df = pd.DataFrame(
                        filtered_records,
                        columns=[
                            "Student ID",
                            "Student Name",
                            "Email",
                            "Date",
                            "Time",
                            "Status",
                            "Latitude",
                            "Longitude",
                            "Distance (m)"
                        ]
                    )

                    st.success(
                        f"Found {len(filtered_records)} attendance record(s)."
                    )

                    st.dataframe(
                        filtered_df,
                        use_container_width=True,
                        hide_index=True
                    )

                    # =================================================
                    # DOWNLOAD FILTERED CSV
                    # =================================================

                    filtered_csv = filtered_df.to_csv(
                        index=False
                    ).encode("utf-8")

                    st.download_button(
                        label="⬇️ Download Filtered Attendance",
                        data=filtered_csv,
                        file_name="filtered_attendance.csv",
                        mime="text/csv",
                        key="filtered_attendance_download"
                    )

                else:

                    st.info(
                        "No attendance records match the selected filters."
                    )

                        
                    # =========================================================
                    # ATTENDANCE MONTH / YEAR FILTER
                    # =========================================================

                    current_date = datetime.now()

                    filter_col1, filter_col2 = st.columns(2)

                    with filter_col1:

                        selected_year = st.number_input(
                            "Select Year",
                            min_value=2020,
                            max_value=2100,
                            value=current_date.year,
                            step=1,
                            key="teacher_attendance_year"
                        )

                    with filter_col2:

                        month_names = [
                            "January",
                            "February",
                            "March",
                            "April",
                            "May",
                            "June",
                            "July",
                            "August",
                            "September",
                            "October",
                            "November",
                            "December"
                        ]

                        selected_month_name = st.selectbox(
                            "Select Month",
                            month_names,
                            index=current_date.month - 1,
                            key="teacher_attendance_month"
                        )

                    selected_month = (
                        month_names.index(selected_month_name) + 1
                    )

                    # =========================================================
                    # GET SELECTED MONTH ATTENDANCE
                    # =========================================================

                    cursor.execute(
                        """
                        SELECT
                            attendance.date,
                            attendance.time,
                            attendance.status,
                            attendance.latitude,
                            attendance.longitude,
                            attendance.distance
                        FROM attendance
                        WHERE attendance.student_id = ?
                        AND strftime('%Y', attendance.date) = ?
                        AND strftime('%m', attendance.date) = ?
                        ORDER BY attendance.date DESC,
                                attendance.time DESC
                        """,
                        (
                            selected_student_id,
                            str(selected_year),
                            f"{selected_month:02d}"
                        )
                    )

                    student_attendance = cursor.fetchall()  

                    if student_attendance:

                        student_attendance_df = pd.DataFrame(
                            student_attendance,
                            columns=[
                                "Date",
                                "Time",
                                "Status",
                                "Latitude",
                                "Longitude",
                                "Distance (m)"
                            ]
                        )
                        # -----------------------------------------
                        # ATTENDANCE COUNT
                        # -----------------------------------------

                        total_records = len(student_attendance)

                        present_records = sum(
                            1
                            for record in student_attendance
                            if record[2] == "Present"
                        )

                        # -----------------------------------------
                        # SELECTED MONTH / YEAR
                        # -----------------------------------------

                        current_date = datetime.now()

                        selected_year = st.number_input(
                            "Select Year",
                            min_value=2020,
                            max_value=2100,
                            value=current_date.year,
                            step=1,
                            key="teacher_attendance_year"
                        )

                        month_names = [
                            "January",
                            "February",
                            "March",
                            "April",
                            "May",
                            "June",
                            "July",
                            "August",
                            "September",
                            "October",
                            "November",
                            "December"
                        ]

                        selected_month_name = st.selectbox(
                            "Select Month",
                            month_names,
                            index=current_date.month - 1,
                            key="teacher_attendance_month"
                        )

                        selected_month = (
                            month_names.index(selected_month_name) + 1
                        )

                        # -----------------------------------------
                        # SELECTED MONTH PRESENT COUNT
                        # -----------------------------------------

                        cursor.execute(
                            """
                            SELECT COUNT(*)
                            FROM attendance
                            WHERE student_id = ?
                            AND strftime('%Y', date) = ?
                            AND strftime('%m', date) = ?
                            AND status = 'Present'
                            """,
                            (
                                selected_student_id,
                                str(selected_year),
                                f"{selected_month:02d}"
                            )
                        )

                        monthly_present = cursor.fetchone()[0]

                        # -----------------------------------------
                        # TOTAL CLASSES
                        # -----------------------------------------

                        monthly_classes = get_total_classes(
                            int(selected_year),
                            selected_month
                        )

                        # -----------------------------------------
                        # ATTENDANCE PERCENTAGE
                        # -----------------------------------------

                        if monthly_classes > 0:

                            attendance_percentage = (
                                monthly_present / monthly_classes
                            ) * 100

                        else:

                            attendance_percentage = 0

                        # -----------------------------------------
                        # STATISTICS
                        # -----------------------------------------

                        col1, col2, col3, col4 = st.columns(4)

                        with col1:

                            st.metric(
                                "Attendance Records",
                                total_records
                            )

                        with col2:

                            st.metric(
                                "Present",
                                monthly_present
                            )

                        with col3:

                            st.metric(
                                "Total Classes",
                                monthly_classes
                            )

                        with col4:

                            st.metric(
                                "Attendance %",
                                f"{attendance_percentage:.2f}%"
                            )

                    else:

                        st.info(
                            "No attendance records found "
                            "for this student."
                        )

            # =========================================================
            # ATTENDANCE REPORT
            # =========================================================

            elif teacher_menu == "📊 Reports":

                st.subheader("📊 Attendance Report")
                st.write("---")

                current_date = datetime.now()

                # -----------------------------------------------------
                # SELECT YEAR
                # -----------------------------------------------------

                report_year = st.number_input(
                    "Select Year",
                    min_value=2020,
                    max_value=2100,
                    value=current_date.year,
                    step=1,
                    key="report_year"
                )

                # -----------------------------------------------------
                # SELECT MONTH
                # -----------------------------------------------------

                report_month_names = [
                    "January",
                    "February",
                    "March",
                    "April",
                    "May",
                    "June",
                    "July",
                    "August",
                    "September",
                    "October",
                    "November",
                    "December"
                ]

                report_month_name = st.selectbox(
                    "Select Month",
                    report_month_names,
                    index=current_date.month - 1,
                    key="report_month"
                )

                report_month = (
                    report_month_names.index(report_month_name) + 1
                )

                # -----------------------------------------------------
                # TOTAL CLASSES
                # -----------------------------------------------------

                report_total_classes = get_total_classes(
                    int(report_year),
                    report_month
                )

                st.info(
                    f"Total Classes in {report_month_name} "
                    f"{int(report_year)}: {report_total_classes}"
                )

                # -----------------------------------------------------
                # GET ALL STUDENTS
                # -----------------------------------------------------

                cursor.execute(
                    """
                    SELECT
                        id,
                        name,
                        email
                    FROM students
                    ORDER BY name
                    """
                )

                students = cursor.fetchall()

                report_data = []

                # -----------------------------------------------------
                # CALCULATE ATTENDANCE
                # -----------------------------------------------------

                for student in students:

                    student_db_id = student[0]
                    student_name = student[1]
                    student_email = student[2]

                    cursor.execute(
                        """
                        SELECT COUNT(*)
                        FROM attendance
                        WHERE student_id = ?
                        AND strftime('%Y', date) = ?
                        AND strftime('%m', date) = ?
                        AND status = 'Present'
                        """,
                        (
                            student_db_id,
                            str(report_year),
                            f"{report_month:02d}"
                        )
                    )

                    present = cursor.fetchone()[0]

                    # -------------------------------------------------
                    # ATTENDANCE PERCENTAGE
                    # -------------------------------------------------

                    if report_total_classes > 0:

                        percentage = (
                            present / report_total_classes
                        ) * 100

                    else:

                        percentage = 0

                    report_data.append(
                        [
                            student_name,
                            student_email,
                            present,
                            report_total_classes,
                            round(percentage, 2)
                        ]
                    )

                # -----------------------------------------------------
                # DISPLAY REPORT
                # -----------------------------------------------------

                if report_data:

                    report_df = pd.DataFrame(
                        report_data,
                        columns=[
                            "Student Name",
                            "Email",
                            "Present",
                            "Total Classes",
                            "Attendance %"
                        ]
                    )

                    st.dataframe(
                        report_df,
                        use_container_width=True,
                        hide_index=True
                    )

                    # -------------------------------------------------
                    # EXPORT CSV
                    # -------------------------------------------------

                    st.write("---")

                    st.subheader("📥 Export Attendance Report")

                    csv_data = report_df.to_csv(
                        index=False
                    ).encode("utf-8")

                    st.download_button(
                        label="📥 Download CSV Report",
                        data=csv_data,
                        file_name=(
                            f"Attendance_Report_"
                            f"{report_month_name}_"
                            f"{int(report_year)}.csv"
                        ),
                        mime="text/csv"
                    )

                else:

                    st.info(
                        "No students registered yet."
                    )



            # =========================================================
            # CLASS SETTINGS
            # =========================================================

            elif teacher_menu == "⚙️ Class Settings":

                st.subheader("⚙️ Class Settings")
                st.write("---")

                st.info(
                    "Set the total number of classes conducted for a particular month."
                )

                # -----------------------------------------------------
                # SELECT YEAR
                # -----------------------------------------------------

                current_year = datetime.now().year

                year = st.number_input(
                    "Select Year",
                    min_value=2020,
                    max_value=2100,
                    value=current_year,
                    step=1,
                    key="class_settings_year"
                )

                # -----------------------------------------------------
                # SELECT MONTH
                # -----------------------------------------------------

                month_names = [
                    "January",
                    "February",
                    "March",
                    "April",
                    "May",
                    "June",
                    "July",
                    "August",
                    "September",
                    "October",
                    "November",
                    "December"
                ]

                selected_month_name = st.selectbox(
                    "Select Month",
                    month_names,
                    index=datetime.now().month - 1,
                    key="class_settings_month_name"
                )

                month = month_names.index(selected_month_name) + 1

                # -----------------------------------------------------
                # CHECK EXISTING SETTING
                # -----------------------------------------------------

                default_classes = get_total_classes(
                    int(year),
                    int(month)
                )

                # -----------------------------------------------------
                # TOTAL CLASSES
                # -----------------------------------------------------

                total_classes = st.number_input(
                    "Total Classes",
                    min_value=1,
                    max_value=100,
                    value=int(default_classes),
                    step=1,
                    key="class_settings_total"
                )

                # -----------------------------------------------------
                # SELECTED INFORMATION
                # -----------------------------------------------------

                st.write(
                    f"Selected Month: **{selected_month_name} {int(year)}**"
                )

                st.write(
                    f"Total Classes: **{int(total_classes)}**"
                )

                # -----------------------------------------------------
                # SAVE CLASS SETTING
                # -----------------------------------------------------

                if st.button(
                    "💾 Save Class Setting",
                    key="save_class_setting"
                ):

                    try:

                        save_total_classes(
                            int(year),
                            int(month),
                            int(total_classes)
                        )

                        st.success(
                            f"Total classes saved successfully for "
                            f"{selected_month_name} {int(year)}."
                        )

                    except Exception as e:

                        st.error(
                            f"Unable to save class setting: {e}"
                        )


                # -----------------------------------------------------
                # SAVE BUTTON
                # -----------------------------------------------------

                if st.button(
                    "💾 Save Class Settings",
                    type="primary",
                    key="save_class_settings"
                ):

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
                                total_classes =
                                excluded.total_classes
                            """,
                            (
                                year,
                                month,
                                total_classes
                            )
                        )

                        conn.commit()

                        st.success(
                            f"✅ Class settings saved successfully!"
                        )

                        st.info(
                            f"📅 {month:02d}/{year} → "
                            f"{total_classes} total classes"
                        )

                    except sqlite3.Error as e:

                        conn.rollback()

                        st.error(
                            f"❌ Database Error: {e}"
                        )

                    finally:

                        conn.close()                   


            elif teacher_menu == "📈 Analytics":

                st.subheader(
                    "📈 Attendance Analytics"
                )

                st.write("---")

                selected_month = st.date_input(
                    "Select Month",
                    datetime.now().date(),
                    key="analytics_month"
                )

                year = selected_month.year
                month = selected_month.month

                # =====================================================
                # GET TOTAL CLASSES FOR SELECTED MONTH
                # =====================================================

                monthly_classes = get_total_classes(
                    year,
                    month
                )

                st.info(
                    f"📅 {month:02d}/{year} | "
                    f"Total Classes: **{monthly_classes}**"
                )

                cursor.execute(
                    """
                    SELECT
                        students.name,
                        COUNT(attendance.id)
                    FROM students
                    LEFT JOIN attendance
                    ON students.id =
                       attendance.student_id
                    AND strftime(
                        '%Y',
                        attendance.date
                    ) = ?
                    AND strftime(
                        '%m',
                        attendance.date
                    ) = ?
                    GROUP BY students.id
                    ORDER BY students.name
                    """,
                    (
                        str(year),
                        f"{month:02d}"
                    )
                )

                analytics_records = cursor.fetchall()

                analytics_data = []

                for record in analytics_records:

                    name = record[0]
                    present = record[1]

                    percentage = (
                        present /
                        monthly_classes
                    ) * 100

                    analytics_data.append(
                        {
                            "Student Name": name,
                            "Attendance %": round(
                                percentage,
                                2
                            )
                        }
                    )

                analytics_df = pd.DataFrame(
                    analytics_data
                )

                if not analytics_df.empty:

                    chart_data = analytics_df[
                        [
                            "Student Name",
                            "Attendance %"
                        ]
                    ].set_index(
                        "Student Name"
                    )


                    st.bar_chart(
                        chart_data
                    )


                    st.dataframe(
                        analytics_df,
                        use_container_width=True,
                        hide_index=True
                    )

                else:

                    st.info(
                        "No analytics data available."
                    )

            # =================================================
            # EXPORT
            # =================================================

            elif teacher_menu == "📥 Export":

                st.subheader(
                    "📥 Export Attendance"
                )

                st.write("---")

                # =================================================
                # DATE RANGE
                # =================================================

                st.subheader(
                    "📅 Select Date Range"
                )

                col1, col2 = st.columns(2)

                with col1:

                    start_date = st.date_input(
                        "Start Date",
                        datetime.now().date(),
                        key="export_start_date"
                    )

                with col2:

                    end_date = st.date_input(
                        "End Date",
                        datetime.now().date(),
                        key="export_end_date"
                    )

                # =================================================
                # VALIDATION
                # =================================================

                if start_date > end_date:

                    st.error(
                        "❌ Start Date cannot be after End Date."
                    )

                else:

                    start_date_string = start_date.strftime(
                        "%Y-%m-%d"
                    )

                    end_date_string = end_date.strftime(
                        "%Y-%m-%d"
                    )

                    # =================================================
                    # GET ATTENDANCE
                    # =================================================

                    cursor.execute(
                        """
                        SELECT
                            students.name,
                            attendance.date,
                            attendance.time,
                            attendance.status,
                            attendance.latitude,
                            attendance.longitude,
                            attendance.distance
                        FROM attendance

                        JOIN students
                        ON students.id =
                        attendance.student_id

                        WHERE attendance.date
                        BETWEEN ? AND ?

                        ORDER BY
                            attendance.date DESC,
                            attendance.time DESC
                        """,
                        (
                            start_date_string,
                            end_date_string
                        )
                    )

                    records = cursor.fetchall()

                    # =================================================
                    # CREATE DATAFRAME
                    # =================================================

                    if records:

                        export_df = pd.DataFrame(
                            records,
                            columns=[
                                "Student Name",
                                "Date",
                                "Time",
                                "Status",
                                "Latitude",
                                "Longitude",
                                "Distance (m)"
                            ]
                        )

                        # =================================================
                        # PREVIEW
                        # =================================================

                        st.write("---")

                        st.subheader(
                            "📊 Export Preview"
                        )

                        st.info(
                            f"Total Records: **{len(export_df)}**"
                        )

                        st.dataframe(
                            export_df,
                            use_container_width=True,
                            hide_index=True
                        )

                        # =================================================
                        # CSV DOWNLOAD
                        # =================================================

                        csv = export_df.to_csv(
                            index=False
                        ).encode("utf-8")

                        # =================================================
                        # EXCEL DOWNLOAD
                        # =================================================

                        excel_buffer = BytesIO()

                        with pd.ExcelWriter(
                            excel_buffer,
                            engine="openpyxl"
                        ) as writer:

                            export_df.to_excel(
                                writer,
                                index=False,
                                sheet_name="Attendance"
                            )

                        excel_data = excel_buffer.getvalue()
                        st.download_button(
                            label="⬇️ Download Attendance CSV",
                            data=csv,
                            file_name=(
                                f"attendance_"
                                f"{start_date_string}_"
                                f"to_"
                                f"{end_date_string}.csv"
                            ),
                            mime="text/csv",
                            key="download_csv"
                        )

                        st.download_button(
                            label="📊 Download Attendance Excel",
                            data=excel_data,
                            file_name=(
                                f"attendance_"
                                f"{start_date_string}_"
                                f"to_"
                                f"{end_date_string}.xlsx"
                            ),
                            mime=(
                                "application/vnd.openxmlformats-officedocument."
                                "spreadsheetml.sheet"
                            ),
                            key="download_excel"
                        )

                    else:

                        st.info(
                            "No attendance records found "
                            "for the selected date range."
                        )

        except sqlite3.Error as e:

            st.error(
                f"❌ Database Error: {e}"
            )

        finally:

            conn.close()

        # =================================================
        # TEACHER LOGOUT
        # =================================================

        st.write("---")

        if st.button(
            "🚪 Teacher Logout",
            key="teacher_logout"
        ):
            st.session_state.teacher_logged_in = False
            st.session_state.teacher_id = None
            st.session_state.teacher_name = ""

            st.rerun()

    # =====================================================
    # TEACHER DASHBOARD WITHOUT LOGIN
    # =====================================================

    elif choice == "Teacher Dashboard":

        st.warning(
            "🔒 Please log in first to access the Teacher Dashboard."
        )

        st.info(
            "Select 'Teacher Login' from the Sidebar Menu to log in."
        )