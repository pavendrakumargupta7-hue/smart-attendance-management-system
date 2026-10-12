import streamlit as st
import sqlite3
import os
import pandas as pd
from datetime import datetime


# =========================================================
# DATABASE
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DB_PATH = os.path.join(
    BASE_DIR,
    "students.db"
)


def get_connection():
    return sqlite3.connect(
        DB_PATH,
        check_same_thread=False
    )


# =========================================================
# TEACHER LOGOUT
# =========================================================

def teacher_logout():

    st.session_state.teacher_logged_in = False
    st.session_state.teacher_id = None
    st.session_state.teacher_name = ""
    st.session_state.teacher = None
    st.session_state.teacher_menu = "Dashboard"

    st.rerun()


# =========================================================
# TEACHER DASHBOARD
# =========================================================

def teacher_dashboard():

    # =====================================================
    # LOGIN CHECK
    # =====================================================

    if not st.session_state.get(
        "teacher_logged_in",
        False
    ):

        st.warning(
            "🔒 Please login as Teacher first."
        )

        return

    # =====================================================
    # GET CURRENT TEACHER
    # =====================================================

    teacher = st.session_state.get(
        "teacher"
    )

    teacher_db_id = st.session_state.get(
        "teacher_id"
    )

    teacher_name = st.session_state.get(
        "teacher_name",
        ""
    )

    # =====================================================
    # SAFETY CHECK
    # =====================================================

    if not teacher or not teacher_db_id:

        st.warning(
            "⚠️ Teacher session not found. Please login again."
        )

        return

    # =====================================================
    # HEADER
    # =====================================================

    st.title(
        "👨‍🏫 Teacher Dashboard"
    )

    st.success(
        f"Welcome {teacher_name} Sir! 👋"
    )

    # =====================================================
    # TEACHER PROFILE
    # =====================================================

    with st.expander(
        "👤 Teacher Profile",
        expanded=False
    ):

        col1, col2 = st.columns(2)

        with col1:

            st.write(
                f"**Teacher Name:** "
                f"{teacher.get('name', '')}"
            )

            st.write(
                f"**Teacher ID:** "
                f"{teacher.get('teacher_id', '')}"
            )

        with col2:

            st.write(
                f"**Email:** "
                f"{teacher.get('email', '')}"
            )

            st.write(
                f"**Teacher Database ID:** "
                f"{teacher_db_id}"
            )

    st.divider()

    # =====================================================
    # MENU
    # =====================================================

    menu_options = [
        "Dashboard",
        "Student Registration",
        "My Students",
        "Attendance Management",
        "Class Settings",
        "Reports",
        "Analytics",
        "Export"
    ]

    teacher_menu = st.radio(
        "Teacher Menu",
        menu_options,
        horizontal=True,
        key="teacher_dashboard_menu"
    )

    st.divider()

    # =====================================================
    # DASHBOARD
    # =====================================================

    if teacher_menu == "Dashboard":

        show_teacher_dashboard(
            teacher_db_id
        )

    # =====================================================
    # STUDENT REGISTRATION
    # =====================================================

    elif teacher_menu == "Student Registration":

        show_student_registration(
            teacher_db_id
        )

    # =====================================================
    # MY STUDENTS
    # =====================================================

    elif teacher_menu == "My Students":

        show_my_students(
            teacher_db_id
        )

    # =====================================================
    # ATTENDANCE MANAGEMENT
    # =====================================================

    elif teacher_menu == "Attendance Management":

        show_attendance_management(
            teacher_db_id
        )

    # =====================================================
    # CLASS SETTINGS
    # =====================================================

    elif teacher_menu == "Class Settings":

        show_class_settings(
            teacher_db_id
        )

    # =====================================================
    # REPORTS
    # =====================================================

    elif teacher_menu == "Reports":

        show_reports(
            teacher_db_id
        )

    # =====================================================
    # ANALYTICS
    # =====================================================

    elif teacher_menu == "Analytics":

        show_analytics(
            teacher_db_id
        )

    # =====================================================
    # EXPORT
    # =====================================================

    elif teacher_menu == "Export":

        show_export(
            teacher_db_id
        )

    # =====================================================
    # LOGOUT
    # =====================================================

    st.divider()

    if st.button(
        "🚪 Teacher Logout",
        key="teacher_dashboard_logout"
    ):

        teacher_logout()


# =========================================================
# DASHBOARD OVERVIEW
# =========================================================

def show_teacher_dashboard(
    teacher_db_id
):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        # -------------------------------------------------
        # TOTAL ASSIGNED STUDENTS
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM teacher_student
            WHERE teacher_id = ?
            """,
            (teacher_db_id,)
        )

        total_students = cursor.fetchone()[0]

        # -------------------------------------------------
        # TODAY
        # -------------------------------------------------

        today = datetime.now().strftime(
            "%Y-%m-%d"
        )

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM attendance a
            INNER JOIN teacher_student ts
                ON a.student_id = ts.student_id
            WHERE ts.teacher_id = ?
            AND a.date = ?
            """,
            (
                teacher_db_id,
                today
            )
        )

        present_today = cursor.fetchone()[0]

        # -------------------------------------------------
        # TOTAL ATTENDANCE
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM attendance a
            INNER JOIN teacher_student ts
                ON a.student_id = ts.student_id
            WHERE ts.teacher_id = ?
            """,
            (teacher_db_id,)
        )

        total_attendance = cursor.fetchone()[0]

        # -------------------------------------------------
        # ABSENT TODAY
        # -------------------------------------------------

        absent_today = max(
            total_students - present_today,
            0
        )

        # -------------------------------------------------
        # ATTENDANCE PERCENTAGE
        # -------------------------------------------------

        if total_students > 0:

            attendance_percentage = (
                present_today /
                total_students
            ) * 100

        else:

            attendance_percentage = 0

        # -------------------------------------------------
        # DASHBOARD
        # -------------------------------------------------

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
                f"{attendance_percentage:.2f}%"
            )

        with col5:

            st.metric(
                "Total Attendance",
                total_attendance
            )

        st.divider()

        # -------------------------------------------------
        # TODAY'S ATTENDANCE
        # -------------------------------------------------

        st.subheader(
            "📅 Today's Attendance"
        )

        cursor.execute(
            """
            SELECT
                s.name,
                s.email,
                a.date,
                a.time,
                a.status,
                a.distance
            FROM attendance a
            INNER JOIN students s
                ON a.student_id = s.id
            INNER JOIN teacher_student ts
                ON s.id = ts.student_id
            WHERE ts.teacher_id = ?
            AND a.date = ?
            ORDER BY a.time DESC
            """,
            (
                teacher_db_id,
                today
            )
        )

        records = cursor.fetchall()

        if records:

            df = pd.DataFrame(
                records,
                columns=[
                    "Student Name",
                    "Email",
                    "Date",
                    "Time",
                    "Status",
                    "Distance"
                ]
            )

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "No attendance recorded today."
            )

    except Exception as e:

        st.error(
            f"Dashboard error: {e}"
        )

    finally:

        conn.close()


# =========================================================
# STUDENT REGISTRATION
# =========================================================

def show_student_registration(
    teacher_db_id
):

    st.subheader(
        "👨‍🎓 Student Registration"
    )

    st.info(
        "Student registration module will be connected here."
    )

    st.write(
        f"Current Teacher ID: {teacher_db_id}"
    )


# =========================================================
# MY STUDENTS
# =========================================================

def show_my_students(
    teacher_db_id
):

    st.subheader(
        "👥 My Students"
    )

    conn = get_connection()

    try:

        query = """
            SELECT
                s.id,
                s.student_id,
                s.name,
                s.email,
                s.course,
                s.semester
            FROM students s
            INNER JOIN teacher_student ts
                ON s.id = ts.student_id
            WHERE ts.teacher_id = ?
            ORDER BY s.name
        """

        df = pd.read_sql_query(
            query,
            conn,
            params=(teacher_db_id,)
        )

        if df.empty:

            st.info(
                "No students are assigned to you."
            )

        else:

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

    except Exception as e:

        st.error(
            f"My Students error: {e}"
        )

    finally:

        conn.close()


# =========================================================
# ATTENDANCE MANAGEMENT
# =========================================================

def show_attendance_management(
    teacher_db_id
):

    st.subheader(
        "📋 Attendance Management"
    )

    conn = get_connection()

    try:

        query = """
            SELECT
                s.name AS student_name,
                s.email,
                a.date,
                a.time,
                a.status,
                a.distance
            FROM attendance a
            INNER JOIN students s
                ON a.student_id = s.id
            INNER JOIN teacher_student ts
                ON s.id = ts.student_id
            WHERE ts.teacher_id = ?
            ORDER BY a.date DESC, a.time DESC
        """

        df = pd.read_sql_query(
            query,
            conn,
            params=(teacher_db_id,)
        )

        if df.empty:

            st.info(
                "No attendance records found."
            )

        else:

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

    except Exception as e:

        st.error(
            f"Attendance Management error: {e}"
        )

    finally:

        conn.close()


# =========================================================
# CLASS SETTINGS
# =========================================================

def show_class_settings(
    teacher_db_id
):

    st.subheader(
        "⚙️ Class Settings"
    )

    st.info(
        "Teacher-specific class settings will be connected here."
    )

    st.write(
        f"Teacher ID: {teacher_db_id}"
    )


# =========================================================
# REPORTS
# =========================================================

def show_reports(
    teacher_db_id
):

    st.subheader(
        "📈 Reports"
    )

    conn = get_connection()

    try:

        query = """
            SELECT
                s.name AS student_name,
                COUNT(a.id) AS attendance_count
            FROM students s
            INNER JOIN teacher_student ts
                ON s.id = ts.student_id
            LEFT JOIN attendance a
                ON s.id = a.student_id
            WHERE ts.teacher_id = ?
            GROUP BY s.id, s.name
            ORDER BY s.name
        """

        df = pd.read_sql_query(
            query,
            conn,
            params=(teacher_db_id,)
        )

        if df.empty:

            st.info(
                "No report data available."
            )

        else:

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

    except Exception as e:

        st.error(
            f"Reports error: {e}"
        )

    finally:

        conn.close()


# =========================================================
# ANALYTICS
# =========================================================

def show_analytics(
    teacher_db_id
):

    st.subheader(
        "📊 Analytics"
    )

    conn = get_connection()

    try:

        query = """
            SELECT
                s.name AS student_name,
                COUNT(a.id) AS attendance_count
            FROM students s
            INNER JOIN teacher_student ts
                ON s.id = ts.student_id
            LEFT JOIN attendance a
                ON s.id = a.student_id
            WHERE ts.teacher_id = ?
            GROUP BY s.id, s.name
            ORDER BY attendance_count DESC
        """

        df = pd.read_sql_query(
            query,
            conn,
            params=(teacher_db_id,)
        )

        if df.empty:

            st.info(
                "No analytics data available."
            )

        else:

            st.bar_chart(
                df.set_index(
                    "student_name"
                )["attendance_count"]
            )

    except Exception as e:

        st.error(
            f"Analytics error: {e}"
        )

    finally:

        conn.close()


# =========================================================
# EXPORT
# =========================================================

def show_export(
    teacher_db_id
):

    st.subheader(
        "📥 Export / Download"
    )

    conn = get_connection()

    try:

        query = """
            SELECT
                s.student_id,
                s.name,
                s.email,
                a.date,
                a.time,
                a.status,
                a.distance
            FROM attendance a
            INNER JOIN students s
                ON a.student_id = s.id
            INNER JOIN teacher_student ts
                ON s.id = ts.student_id
            WHERE ts.teacher_id = ?
            ORDER BY a.date DESC, a.time DESC
        """

        df = pd.read_sql_query(
            query,
            conn,
            params=(teacher_db_id,)
        )

        if df.empty:

            st.warning(
                "No attendance data available for export."
            )

        else:

            st.write(
                f"Total Records: {len(df)}"
            )

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            # ---------------------------------------------
            # CSV DOWNLOAD
            # ---------------------------------------------

            csv_data = df.to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                label="⬇️ Download CSV",
                data=csv_data,
                file_name=(
                    "teacher_attendance_report.csv"
                ),
                mime="text/csv",
                key="teacher_csv_download"
            )

    except Exception as e:

        st.error(
            f"Export error: {e}"
        )

    finally:

        conn.close()