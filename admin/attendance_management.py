import streamlit as st
import sqlite3


DB_NAME = "students.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def attendance_management():

    # =====================================================
    # ADMIN LOGIN CHECK
    # =====================================================

    if not st.session_state.get("admin_logged_in", False):
        st.warning("🔒 Please login as Admin first.")
        return

    st.subheader("📋 Attendance Management")

    # =====================================================
    # ATTENDANCE MENU
    # =====================================================

    attendance_menu = st.selectbox(
        "Select Attendance Menu",
        [
            "View All Attendance",
            "Search Attendance",
            "Student Attendance"
        ],
        key="admin_attendance_menu"
    )

    # =====================================================
    # VIEW ALL ATTENDANCE
    # =====================================================

    if attendance_menu == "View All Attendance":

        st.write("---")
        st.subheader("📊 All Attendance Records")

        conn = get_connection()

        rows = conn.execute("""
            SELECT
                a.id AS attendance_id,
                a.student_id AS attendance_student_id,
                s.id AS student_db_id,
                s.student_id AS student_id_text,
                s.name AS student_name,
                s.email AS student_email,
                a.date,
                a.time,
                a.status,
                a.latitude,
                a.longitude,
                a.distance
            FROM attendance AS a
            LEFT JOIN students AS s
                ON CAST(a.student_id AS INTEGER) = s.id
            ORDER BY a.date DESC, a.time DESC
        """).fetchall()

        conn.close()

        if rows:

            data = []

            for row in rows:

                # -----------------------------------------
                # Student ID
                # -----------------------------------------

                display_student_id = row["student_id_text"]

                if display_student_id is None:
                    display_student_id = "Student not found"

                # -----------------------------------------
                # Student Name
                # -----------------------------------------

                display_name = row["student_name"]

                if display_name is None:
                    display_name = "Student not found"

                # -----------------------------------------
                # Email
                # -----------------------------------------

                display_email = row["student_email"]

                if display_email is None:
                    display_email = "Not available"

                data.append({
                    "ID": row["attendance_id"],
                    "Student ID": display_student_id,
                    "Student Name": display_name,
                    "Email": display_email,
                    "Date": row["date"],
                    "Time": row["time"],
                    "Status": row["status"],
                    "Latitude": row["latitude"],
                    "Longitude": row["longitude"],
                    "Distance (m)": row["distance"]
                })

            st.dataframe(
                data,
                use_container_width=True,
                hide_index=True
            )

            st.info(
                f"Total Attendance Records: {len(rows)}"
            )

        else:

            st.info(
                "No attendance records found."
            )


    # =====================================================
    # SEARCH ATTENDANCE
    # =====================================================

    elif attendance_menu == "Search Attendance":

        st.write("---")
        st.subheader("🔎 Search Attendance")

        search_text = st.text_input(
            "Search by Student ID, Name or Email",
            key="admin_attendance_search"
        )

        search_date = st.text_input(
            "Search by Date (YYYY-MM-DD)",
            placeholder="Example: 2026-09-30",
            key="admin_attendance_date_search"
        )

        if st.button(
            "🔍 Search Attendance",
            key="admin_search_attendance_btn"
        ):

            conn = get_connection()

            try:
                query = """
                    SELECT
                        a.id,
                        a.student_id,
                        s.student_id AS student_id_text,
                        s.name,
                        s.email,
                        a.date,
                        a.time,
                        a.status,
                        a.latitude,
                        a.longitude,
                        a.distance
                    FROM attendance a
                    LEFT JOIN students s
                        ON a.student_id = s.id
                    WHERE 1=1
                """

                params = []

                # =============================================
                # SEARCH STUDENT
                # =============================================

                if search_text.strip():

                    query += """
                        AND (
                            s.student_id LIKE ?
                            OR s.name LIKE ?
                            OR s.email LIKE ?
                        )
                    """

                    value = f"%{search_text.strip()}%"

                    params.extend([
                        value,
                        value,
                        value
                    ])

                # =============================================
                # SEARCH DATE
                # =============================================

                if search_date.strip():

                    query += """
                        AND a.date = ?
                    """

                    params.append(search_date.strip())

                query += """
                    ORDER BY a.date DESC, a.time DESC
                """

                rows = conn.execute(
                    query,
                    params
                ).fetchall()

                st.info(
                    f"DEBUG: Search button executed. "
                    f"Rows returned: {len(rows)}"
                )

                if rows:

                    data = []

                    for row in rows:

                        data.append({
                            "ID": row["id"],
                            "Student ID": row["student_id_text"],
                            "Student Name": row["name"],
                            "Email": row["email"],
                            "Date": row["date"],
                            "Time": row["time"],
                            "Status": row["status"],
                            "Latitude": row["latitude"],
                            "Longitude": row["longitude"],
                            "Distance (m)": row["distance"]
                        })

                    st.dataframe(
                        data,
                        use_container_width=True,
                        hide_index=True
                    )

                    st.success(
                        f"{len(rows)} attendance record(s) found."
                    )

                else:

                    st.warning(
                        "No attendance records found."
                    )

            except Exception as e:

                st.error(
                    f"Attendance search failed: {e}"
                )

            finally:
                conn.close()

            if rows:

                data = []

                for row in rows:

                    data.append({
                        "ID": row["id"],
                        "Student ID": row["student_id_text"],
                        "Student Name": row["name"],
                        "Email": row["email"],
                        "Date": row["date"],
                        "Time": row["time"],
                        "Status": row["status"],
                        "Latitude": row["latitude"],
                        "Longitude": row["longitude"],
                        "Distance (m)": row["distance"]
                    })

                st.dataframe(
                    data,
                    use_container_width=True,
                    hide_index=True
                )

                st.success(
                    f"{len(rows)} attendance record(s) found."
                )

            else:

                st.warning(
                    "No attendance records found."
                )

    # =====================================================
    # STUDENT ATTENDANCE
    # =====================================================

    elif attendance_menu == "Student Attendance":

        st.write("---")
        st.subheader("👤 Student Attendance")

        conn = get_connection()

        students = conn.execute("""
            SELECT
                id,
                student_id,
                name,
                email
            FROM students
            ORDER BY name
        """).fetchall()

        conn.close()

        if not students:

            st.info(
                "No students found."
            )

            return

        student_options = {
            f"{student['name']} ({student['student_id']})":
            student["id"]
            for student in students
        }

        selected_student = st.selectbox(
            "Select Student",
            list(student_options.keys()),
            key="admin_attendance_student_select"
        )

        # This is students.id
        selected_student_id = student_options[
            selected_student
        ]

        conn = get_connection()

        # =================================================
        # STUDENT INFORMATION
        # =================================================

        student = conn.execute("""
            SELECT
                id,
                student_id,
                name,
                email,
                course,
                semester
            FROM students
            WHERE id = ?
        """, (
            selected_student_id,
        )).fetchone()

        # =================================================
        # STUDENT ATTENDANCE
        # =================================================

        attendance_records = conn.execute("""
            SELECT
                id,
                date,
                time,
                status,
                latitude,
                longitude,
                distance
            FROM attendance
            WHERE student_id = ?
            ORDER BY date DESC, time DESC
        """, (
            selected_student_id,
        )).fetchall()

        conn.close()

        # =================================================
        # STUDENT INFORMATION
        # =================================================

        if student:

            st.write("---")
            st.subheader("🎓 Student Information")

            col1, col2 = st.columns(2)

            with col1:

                st.write(
                    f"**Student ID:** "
                    f"{student['student_id']}"
                )

                st.write(
                    f"**Name:** "
                    f"{student['name']}"
                )

                st.write(
                    f"**Email:** "
                    f"{student['email'] or 'Not provided'}"
                )

            with col2:

                st.write(
                    f"**Course:** "
                    f"{student['course'] or 'Not provided'}"
                )

                st.write(
                    f"**Semester:** "
                    f"{student['semester'] or 'Not provided'}"
                )

        # =================================================
        # ATTENDANCE RECORDS
        # =================================================

        st.write("---")
        st.subheader("📅 Attendance Records")

        if attendance_records:

            total_records = len(
                attendance_records
            )

            present_count = sum(
                1
                for record in attendance_records
                if record["status"] == "Present"
            )

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "Total Attendance",
                    total_records
                )

            with col2:

                st.metric(
                    "Present",
                    present_count
                )

            data = []

            for record in attendance_records:

                data.append({
                    "Date": record["date"],
                    "Time": record["time"],
                    "Status": record["status"],
                    "Latitude": record["latitude"],
                    "Longitude": record["longitude"],
                    "Distance (m)": record["distance"]
                })

            st.dataframe(
                data,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "No attendance records found "
                "for this student."
            )