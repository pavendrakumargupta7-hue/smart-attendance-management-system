import streamlit as st
import sqlite3
import hashlib
from datetime import datetime


# =====================================================
# DATABASE
# =====================================================

DB_NAME = "students.db"


# =====================================================
# PASSWORD HASH
# =====================================================

def hash_password(password):

    return hashlib.sha256(
        password.encode()
    ).hexdigest()


# =====================================================
# DATABASE CONNECTION
# =====================================================

def get_connection():

    conn = sqlite3.connect(DB_NAME)

    conn.row_factory = sqlite3.Row

    return conn


# =====================================================
# STUDENT MANAGEMENT
# =====================================================

def student_management():

    # -------------------------------------------------
    # ADMIN LOGIN CHECK
    # -------------------------------------------------

    if not st.session_state.get(
        "admin_logged_in",
        False
    ):

        st.warning(
            "🔒 Please login as Admin first."
        )

        return

    st.subheader(
        "👨‍🎓 Student Management"
    )


    # =================================================
    # STUDENT ACTION MENU
    # =================================================

    action = st.selectbox(

        "Select Action",

        [
            "View Students",
            "Search Student",
            "Student Profile",
            "Edit Student",
            "Remove Student"
        ],

        key="admin_student_management_action"
    )


    # =================================================
    # VIEW STUDENTS
    # =================================================

    if action == "View Students":

        st.write("### 👥 All Students")

        conn = get_connection()

        try:

            students = conn.execute(
                """
                SELECT
                    id,
                    student_id,
                    name,
                    email,
                    created_at
                FROM students
                ORDER BY name
                """
            ).fetchall()

        finally:

            conn.close()


        if not students:

            st.info(
                "No students found."
            )

            return


        st.write(
            f"**Total Students: {len(students)}**"
        )

        st.write("---")


        # -------------------------------------------------
        # STUDENT CARDS
        # -------------------------------------------------

        for student in students:

            student_db_id = student["id"]

            student_id = student["student_id"]

            student_name = student["name"]

            student_email = (
                student["email"]
                if student["email"]
                else "Not provided"
            )

            registered_date = (
                student["created_at"]
                if student["created_at"]
                else "Not available"
            )


            # =================================================
            # ATTENDANCE COUNT
            # =================================================

            conn = get_connection()

            try:

                attendance_count = conn.execute(
                    """
                    SELECT COUNT(*)
                    FROM attendance
                    WHERE student_id = ?
                    AND status = 'Present'
                    """,
                    (student_db_id,)
                ).fetchone()[0]

            finally:

                conn.close()


            # =================================================
            # STUDENT ID DISPLAY
            # =================================================

            display_student_id = (

                student_id
                if student_id
                else "Not Assigned"

            )


            # =================================================
            # STUDENT EXPANDER
            # =================================================

            with st.expander(
                f"👨‍🎓 {student_name} "
                f"({display_student_id})"
            ):

                # =============================================
                # STUDENT INFORMATION
                # =============================================

                col1, col2 = st.columns(2)


                with col1:

                    st.write(
                        f"**🆔 Student ID:** "
                        f"{display_student_id}"
                    )

                    st.write(
                        f"**👤 Name:** "
                        f"{student_name}"
                    )

                    st.write(
                        f"**📧 Email:** "
                        f"{student_email}"
                    )


                with col2:

                    st.write(
                        f"**📅 Registered Date:** "
                        f"{registered_date}"
                    )

                    st.metric(
                        "📊 Total Attendance",
                        attendance_count
                    )


                st.write("---")


                # =============================================
                # ATTENDANCE CONTROL
                # =============================================

                st.write(
                    "### 📋 Attendance Control"
                )


                add_col, count_col, remove_col = st.columns(
                    [1, 2, 1]
                )


                # =================================================
                # ADD ATTENDANCE
                # =================================================

                with add_col:

                    if st.button(
                        "➕ Add",
                        key=f"add_attendance_{student_db_id}"
                    ):

                        conn = get_connection()

                        try:

                            today = datetime.now().strftime(
                                "%Y-%m-%d"
                            )

                            current_time = datetime.now().strftime(
                                "%H:%M:%S"
                            )


                            # -------------------------------------
                            # CHECK TODAY'S ATTENDANCE
                            # -------------------------------------

                            existing = conn.execute(
                                """
                                SELECT id
                                FROM attendance
                                WHERE student_id = ?
                                AND date = ?
                                LIMIT 1
                                """,
                                (
                                    student_db_id,
                                    today
                                )
                            ).fetchone()


                            if existing:

                                st.warning(
                                    "⚠️ Attendance is already "
                                    "marked for today."
                                )


                            else:

                                conn.execute(
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
                                        student_db_id,
                                        today,
                                        current_time,
                                        "Present",
                                        None,
                                        None,
                                        None
                                    )
                                )

                                conn.commit()

                                st.success(
                                    "✅ Attendance added."
                                )

                                st.rerun()

                        except sqlite3.IntegrityError:

                            st.warning(
                                "⚠️ Attendance already exists "
                                "for today."
                            )

                        except Exception as e:

                            conn.rollback()

                            st.error(
                                f"❌ Database Error: {e}"
                            )

                        finally:

                            conn.close()


                # =================================================
                # CURRENT ATTENDANCE COUNT
                # =================================================

                with count_col:

                    st.metric(
                        "Total Attendance",
                        attendance_count
                    )


                # =================================================
                # REMOVE LATEST ATTENDANCE
                # =================================================

                with remove_col:

                    if st.button(
                        "➖ Remove",
                        key=f"remove_attendance_{student_db_id}"
                    ):

                        conn = get_connection()

                        try:

                            latest_record = conn.execute(
                                """
                                SELECT id
                                FROM attendance
                                WHERE student_id = ?
                                AND status = 'Present'
                                ORDER BY
                                    date DESC,
                                    time DESC,
                                    id DESC
                                LIMIT 1
                                """,
                                (student_db_id,)
                            ).fetchone()


                            if latest_record:

                                conn.execute(
                                    """
                                    DELETE FROM attendance
                                    WHERE id = ?
                                    """,
                                    (
                                        latest_record["id"],
                                    )
                                )

                                conn.commit()

                                st.success(
                                    "✅ Latest attendance removed."
                                )

                                st.rerun()

                            else:

                                st.warning(
                                    "⚠️ No attendance record "
                                    "available to remove."
                                )

                        except Exception as e:

                            conn.rollback()

                            st.error(
                                f"❌ Database Error: {e}"
                            )

                        finally:

                            conn.close()


    # =================================================
    # SEARCH STUDENT
    # =================================================

    elif action == "Search Student":

        st.write("### 🔎 Search Student")


        search_text = st.text_input(

            "Search by Student ID, Name or Email",

            placeholder="Enter search text...",

            key="admin_student_search"
        )


        if search_text.strip():

            conn = get_connection()

            try:

                search_value = (
                    f"%{search_text.strip()}%"
                )


                students = conn.execute(
                    """
                    SELECT
                        id,
                        student_id,
                        name,
                        email,
                        created_at
                    FROM students
                    WHERE
                        student_id LIKE ?
                        OR name LIKE ?
                        OR email LIKE ?
                    ORDER BY name
                    """,
                    (
                        search_value,
                        search_value,
                        search_value
                    )
                ).fetchall()

            finally:

                conn.close()


            if not students:

                st.warning(
                    "No matching student found."
                )


            else:

                st.success(
                    f"{len(students)} student(s) found."
                )


                for student in students:

                    conn = get_connection()

                    try:

                        attendance_count = conn.execute(
                            """
                            SELECT COUNT(*)
                            FROM attendance
                            WHERE student_id = ?
                            AND status = 'Present'
                            """,
                            (student["id"],)
                        ).fetchone()[0]

                    finally:

                        conn.close()


                    student_id = (

                        student["student_id"]
                        if student["student_id"]
                        else "Not Assigned"

                    )


                    email = (

                        student["email"]
                        if student["email"]
                        else "Not provided"

                    )


                    registered_date = (

                        student["created_at"]
                        if student["created_at"]
                        else "Not available"

                    )


                    with st.expander(
                        f"👨‍🎓 {student['name']} "
                        f"({student_id})"
                    ):

                        st.write(
                            f"**🆔 Student ID:** "
                            f"{student_id}"
                        )

                        st.write(
                            f"**👤 Name:** "
                            f"{student['name']}"
                        )

                        st.write(
                            f"**📧 Email:** "
                            f"{email}"
                        )

                        st.write(
                            f"**📅 Registered Date:** "
                            f"{registered_date}"
                        )

                        st.metric(
                            "📊 Total Attendance",
                            attendance_count
                        )


    # =================================================
    # STUDENT PROFILE
    # =================================================

    elif action == "Student Profile":

        st.write("### 👤 Student Profile")


        conn = get_connection()

        try:

            students = conn.execute(
                """
                SELECT
                    id,
                    student_id,
                    name
                FROM students
                ORDER BY name
                """
            ).fetchall()

        finally:

            conn.close()


        if not students:

            st.info(
                "No students found."
            )

            return


        student_options = {

            f"{student['name']} "
            f"({student['student_id'] or 'Not Assigned'})":

            student["id"]

            for student in students

        }


        selected_student = st.selectbox(

            "Select Student",

            list(student_options.keys()),

            key="admin_student_profile_select"
        )


        selected_id = student_options[
            selected_student
        ]


        conn = get_connection()

        try:

            student = conn.execute(
                """
                SELECT
                    id,
                    student_id,
                    name,
                    email,
                    created_at
                FROM students
                WHERE id = ?
                """,
                (selected_id,)
            ).fetchone()


            attendance = conn.execute(
                """
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
                """,
                (selected_id,)
            ).fetchall()

        finally:

            conn.close()


        if student:

            st.write("---")


            col1, col2 = st.columns(2)


            # =============================================
            # STUDENT DETAILS
            # =============================================

            with col1:

                st.write(
                    "### 📄 Student Details"
                )


                st.write(
                    f"**🆔 Student ID:** "
                    f"{student['student_id'] or 'Not Assigned'}"
                )


                st.write(
                    f"**👤 Name:** "
                    f"{student['name']}"
                )


                st.write(
                    f"**📧 Email:** "
                    f"{student['email'] or 'Not provided'}"
                )


                st.write(
                    f"**📅 Registered Date:** "
                    f"{student['created_at'] or 'Not available'}"
                )


            # =============================================
            # ATTENDANCE SUMMARY
            # =============================================

            with col2:

                st.write(
                    "### 📊 Attendance"
                )


                total_attendance = len(
                    attendance
                )


                present_count = sum(

                    1
                    for record in attendance
                    if record["status"] == "Present"

                )


                st.metric(
                    "Total Records",
                    total_attendance
                )


                st.metric(
                    "Present",
                    present_count
                )


            # =============================================
            # ATTENDANCE HISTORY
            # =============================================

            if attendance:

                st.write("---")

                st.write(
                    "### 📋 Attendance History"
                )


                attendance_data = []


                for record in attendance:

                    attendance_data.append({

                        "Date":
                            record["date"],

                        "Time":
                            record["time"],

                        "Status":
                            record["status"],

                        "Latitude":
                            record["latitude"],

                        "Longitude":
                            record["longitude"],

                        "Distance (m)":
                            record["distance"]

                    })


                st.dataframe(

                    attendance_data,

                    use_container_width=True,

                    hide_index=True
                )


            else:

                st.info(
                    "No attendance records found."
                )


    # =================================================
    # EDIT STUDENT
    # =================================================

    elif action == "Edit Student":

        st.write("### ✏️ Edit Student")


        conn = get_connection()

        try:

            students = conn.execute(
                """
                SELECT
                    id,
                    student_id,
                    name
                FROM students
                ORDER BY name
                """
            ).fetchall()

        finally:

            conn.close()


        if not students:

            st.info(
                "No students found."
            )

            return


        student_options = {

            f"{student['name']} "
            f"({student['student_id'] or 'Not Assigned'})":

            student["id"]

            for student in students

        }


        selected_student = st.selectbox(

            "Select Student",

            list(student_options.keys()),

            key="admin_edit_student_select"
        )


        selected_id = student_options[
            selected_student
        ]


        conn = get_connection()

        try:

            student = conn.execute(
                """
                SELECT
                    student_id,
                    name,
                    email
                FROM students
                WHERE id = ?
                """,
                (selected_id,)
            ).fetchone()

        finally:

            conn.close()


        if student:

            new_student_id = st.text_input(

                "Student ID",

                value=student["student_id"] or "",

                key="admin_edit_student_id"
            )


            new_name = st.text_input(

                "Student Name",

                value=student["name"] or "",

                key="admin_edit_student_name"
            )


            new_email = st.text_input(

                "Student Email",

                value=student["email"] or "",

                key="admin_edit_student_email"
            )


            new_password = st.text_input(

                "New Password (optional)",

                type="password",

                key="admin_edit_student_password"
            )


            if st.button(

                "💾 Update Student",

                key="admin_update_student_btn"

            ):

                if not new_student_id.strip():

                    st.error(
                        "Student ID cannot be empty."
                    )

                    return


                if not new_name.strip():

                    st.error(
                        "Student Name cannot be empty."
                    )

                    return


                conn = get_connection()

                try:

                    if new_password:

                        conn.execute(
                            """
                            UPDATE students
                            SET
                                student_id = ?,
                                name = ?,
                                email = ?,
                                password = ?
                            WHERE id = ?
                            """,
                            (
                                new_student_id.strip(),
                                new_name.strip(),
                                new_email.strip(),
                                hash_password(
                                    new_password
                                ),
                                selected_id
                            )
                        )

                    else:

                        conn.execute(
                            """
                            UPDATE students
                            SET
                                student_id = ?,
                                name = ?,
                                email = ?
                            WHERE id = ?
                            """,
                            (
                                new_student_id.strip(),
                                new_name.strip(),
                                new_email.strip(),
                                selected_id
                            )
                        )


                    conn.commit()


                    st.success(
                        "✅ Student updated successfully."
                    )


                    st.rerun()


                except sqlite3.IntegrityError:

                    st.error(
                        "❌ This Student ID already exists."
                    )


                except Exception as e:

                    conn.rollback()

                    st.error(
                        f"❌ Database Error: {e}"
                    )


                finally:

                    conn.close()


    # =================================================
    # REMOVE STUDENT
    # =================================================

    elif action == "Remove Student":

        st.write("### 🗑️ Remove Student")


        # -------------------------------------------------
        # LOAD STUDENTS
        # -------------------------------------------------

        conn = get_connection()

        try:

            students = conn.execute(
                """
                SELECT
                    id,
                    student_id,
                    name,
                    email,
                    created_at
                FROM students
                ORDER BY name
                """
            ).fetchall()

        finally:

            conn.close()


        if not students:

            st.info(
                "No students found."
            )

            return


        # -------------------------------------------------
        # STUDENT SELECTION
        # -------------------------------------------------

        student_options = {

            f"{student['name']} "
            f"({student['student_id'] or 'Not Assigned'})":

            student["id"]

            for student in students

        }


        selected_student = st.selectbox(

            "Select Student to Remove",

            list(student_options.keys()),

            key="admin_remove_student_select"
        )


        selected_id = student_options[
            selected_student
        ]


        # -------------------------------------------------
        # GET SELECTED STUDENT
        # -------------------------------------------------

        conn = get_connection()

        try:

            student = conn.execute(
                """
                SELECT
                    id,
                    student_id,
                    name,
                    email,
                    created_at
                FROM students
                WHERE id = ?
                """,
                (selected_id,)
            ).fetchone()


            # ---------------------------------------------
            # ATTENDANCE COUNT
            # ---------------------------------------------

            attendance_count = conn.execute(
                """
                SELECT COUNT(*)
                FROM attendance
                WHERE student_id = ?
                """,
                (selected_id,)
            ).fetchone()[0]


            # ---------------------------------------------
            # FACE PROFILE CHECK
            # ---------------------------------------------

            face_profile = conn.execute(
                """
                SELECT id
                FROM face_profiles
                WHERE student_id = ?
                LIMIT 1
                """,
                (selected_id,)
            ).fetchone()


            # ---------------------------------------------
            # TEACHER ASSIGNMENT COUNT
            # ---------------------------------------------

            teacher_assignment_count = conn.execute(
                """
                SELECT COUNT(*)
                FROM teacher_student
                WHERE student_id = ?
                """,
                (selected_id,)
            ).fetchone()[0]

        finally:

            conn.close()


        if not student:

            st.error(
                "Student not found."
            )

            return


        # =================================================
        # STUDENT INFORMATION
        # =================================================

        st.write("---")

        st.write(
            "### 👤 Student Information"
        )


        col1, col2 = st.columns(2)


        with col1:

            st.write(
                f"**🆔 Student ID:** "
                f"{student['student_id'] or 'Not Assigned'}"
            )

            st.write(
                f"**👤 Name:** "
                f"{student['name']}"
            )

            st.write(
                f"**📧 Email:** "
                f"{student['email'] or 'Not provided'}"
            )


        with col2:

            st.write(
                f"**📅 Registered Date:** "
                f"{student['created_at'] or 'Not available'}"
            )

            st.metric(
                "📋 Attendance Records",
                attendance_count
            )

            st.metric(
                "👨‍🏫 Teacher Assignments",
                teacher_assignment_count
            )


        # =================================================
        # RELATED DATA
        # =================================================

        if face_profile:

            st.info(
                "📷 Face profile is registered."
            )

        else:

            st.info(
                "📷 No face profile found."
            )


        # =================================================
        # WARNING
        # =================================================

        st.warning(
            "⚠️ Removing this student will permanently "
            "delete the student record and its related "
            "attendance, face profile, and teacher "
            "assignment data."
        )


        # =================================================
        # CONFIRMATION
        # =================================================

        confirm_remove = st.checkbox(

            "I understand that this action cannot be undone.",

            key="admin_confirm_student_remove"
        )


        # =================================================
        # REMOVE BUTTON
        # =================================================

        if st.button(

            "🗑️ Remove Student Permanently",

            type="primary",

            key="admin_remove_student_btn"

        ):

            if not confirm_remove:

                st.error(
                    "Please confirm removal first."
                )

                return


            conn = get_connection()

            try:

                # -----------------------------------------
                # DELETE TEACHER ASSIGNMENTS
                # -----------------------------------------

                conn.execute(
                    """
                    DELETE FROM teacher_student
                    WHERE student_id = ?
                    """,
                    (selected_id,)
                )


                # -----------------------------------------
                # DELETE ATTENDANCE
                # -----------------------------------------

                conn.execute(
                    """
                    DELETE FROM attendance
                    WHERE student_id = ?
                    """,
                    (selected_id,)
                )


                # -----------------------------------------
                # DELETE FACE PROFILE
                # -----------------------------------------

                conn.execute(
                    """
                    DELETE FROM face_profiles
                    WHERE student_id = ?
                    """,
                    (selected_id,)
                )


                # -----------------------------------------
                # DELETE STUDENT
                # -----------------------------------------

                cursor = conn.execute(
                    """
                    DELETE FROM students
                    WHERE id = ?
                    """,
                    (selected_id,)
                )


                # -----------------------------------------
                # VERIFY DELETE
                # -----------------------------------------

                if cursor.rowcount == 0:

                    raise Exception(
                        "Student could not be removed."
                    )


                # -----------------------------------------
                # COMMIT
                # -----------------------------------------

                conn.commit()


                st.success(
                    f"✅ Student "
                    f"'{student['name']}' "
                    f"has been removed successfully."
                )


                st.rerun()


            except Exception as e:

                conn.rollback()

                st.error(
                    f"❌ Database Error: {e}"
                )


            finally:

                conn.close()