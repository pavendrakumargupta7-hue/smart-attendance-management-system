import streamlit as st
import sqlite3
import hashlib
import os

# =====================================================
# DATABASE PATH
# =====================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DB_NAME = os.path.join(
    BASE_DIR,
    "students.db"
)


# =====================================================
# PASSWORD HASH
# =====================================================

def hash_password(password):

    return hashlib.sha256(
        password.encode()
    ).hexdigest()


# =====================================================
# PREPARE / MIGRATE TEACHERS TABLE
# =====================================================

def prepare_teacher_table():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:

        # =================================================
        # CREATE TABLE IF NOT EXISTS
        # =================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teachers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id TEXT,
                name TEXT NOT NULL,
                email TEXT,
                password TEXT NOT NULL,
                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # =================================================
        # READ CURRENT COLUMNS
        # =================================================

        cursor.execute(
            "PRAGMA table_info(teachers)"
        )

        columns = {
            column[1]
            for column in cursor.fetchall()
        }

        # =================================================
        # ADD teacher_id IF MISSING
        # =================================================

        if "teacher_id" not in columns:

            cursor.execute("""
                ALTER TABLE teachers
                ADD COLUMN teacher_id TEXT
            """)

        # =================================================
        # ADD created_at IF MISSING
        # =================================================

        if "created_at" not in columns:

            cursor.execute("""
                ALTER TABLE teachers
                ADD COLUMN created_at TIMESTAMP
            """)

            cursor.execute("""
                UPDATE teachers
                SET created_at = CURRENT_TIMESTAMP
                WHERE created_at IS NULL
            """)

        # =================================================
        # GENERATE IDs FOR OLD TEACHERS
        # =================================================

        cursor.execute("""
            SELECT id
            FROM teachers
            WHERE teacher_id IS NULL
               OR TRIM(teacher_id) = ''
            ORDER BY id
        """)

        old_teachers = cursor.fetchall()

        for teacher in old_teachers:

            db_id = teacher[0]

            generated_id = f"T{db_id:03d}"

            cursor.execute(
                """
                UPDATE teachers
                SET teacher_id = ?
                WHERE id = ?
                """,
                (
                    generated_id,
                    db_id
                )
            )

        conn.commit()

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


# =====================================================
# TEACHER MANAGEMENT
# =====================================================

def teacher_management():

    # =================================================
    # ADMIN LOGIN CHECK
    # =================================================

    if not st.session_state.get(
        "admin_logged_in",
        False
    ):

        st.warning(
            "🔒 Please login as Admin first."
        )

        return

    # =================================================
    # PREPARE DATABASE
    # =================================================

    try:

        prepare_teacher_table()

    except Exception as e:

        st.error(
            f"Database setup error: {e}"
        )

        return

    # =================================================
    # PAGE TITLE
    # =================================================

    st.subheader(
        "👨‍🏫 Teacher Management"
    )

    # =================================================
    # MENU
    # =================================================

    teacher_menu = st.radio(
        "Select Action",
        [
            "Add Teacher",
            "View Teachers",
            "Edit Teacher",
            "Delete Teacher"
        ],
        horizontal=True,
        key="admin_teacher_action"
    )

    # =================================================
    # ADD TEACHER
    # =================================================

    if teacher_menu == "Add Teacher":

        st.write(
            "### ➕ Add New Teacher"
        )

        teacher_id = st.text_input(
            "Teacher ID",
            placeholder="Example: T001",
            key="add_teacher_id"
        )

        name = st.text_input(
            "Teacher Name",
            placeholder="Enter teacher name",
            key="add_teacher_name"
        )

        email = st.text_input(
            "Teacher Email",
            placeholder="Enter teacher email",
            key="add_teacher_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="add_teacher_password"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            key="add_teacher_confirm_password"
        )

        if st.button(
            "➕ Add Teacher",
            key="add_teacher_button"
        ):

            if not teacher_id.strip():

                st.error(
                    "Please enter Teacher ID."
                )

                return

            if not name.strip():

                st.error(
                    "Please enter Teacher Name."
                )

                return

            if not email.strip():

                st.error(
                    "Please enter Teacher Email."
                )

                return

            if not password:

                st.error(
                    "Please enter Password."
                )

                return

            if password != confirm_password:

                st.error(
                    "Passwords do not match."
                )

                return

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            try:

                # -----------------------------------------
                # CHECK TEACHER ID
                # -----------------------------------------

                cursor.execute(
                    """
                    SELECT id
                    FROM teachers
                    WHERE teacher_id = ?
                    """,
                    (
                        teacher_id.strip(),
                    )
                )

                if cursor.fetchone():

                    st.error(
                        "❌ Teacher ID already exists."
                    )

                    return

                # -----------------------------------------
                # CHECK EMAIL
                # -----------------------------------------

                cursor.execute(
                    """
                    SELECT id
                    FROM teachers
                    WHERE email = ?
                    """,
                    (
                        email.strip(),
                    )
                )

                if cursor.fetchone():

                    st.error(
                        "❌ Teacher Email already exists."
                    )

                    return

                # -----------------------------------------
                # INSERT
                # -----------------------------------------

                cursor.execute(
                    """
                    INSERT INTO teachers
                    (
                        teacher_id,
                        name,
                        email,
                        password,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (
                        teacher_id.strip(),
                        name.strip(),
                        email.strip(),
                        hash_password(password)
                    )
                )

                conn.commit()

                st.success(
                    f"✅ Teacher '{name}' added successfully."
                )

            except Exception as e:

                conn.rollback()

                st.error(
                    f"Database Error: {e}"
                )

            finally:

                conn.close()

    # =================================================
    # VIEW TEACHERS
    # =================================================

    elif teacher_menu == "View Teachers":

        st.write(
            "### 👥 All Teachers"
        )

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        try:

            cursor.execute(
                """
                SELECT
                    id,
                    teacher_id,
                    name,
                    email,
                    created_at
                FROM teachers
                ORDER BY id DESC
                """
            )

            teachers = cursor.fetchall()

        except Exception as e:

            conn.close()

            st.error(
                f"Database Error: {e}"
            )

            return

        conn.close()

        if not teachers:

            st.info(
                "No teachers found."
            )

        else:

            st.info(
                f"Total Teachers: {len(teachers)}"
            )

            for teacher in teachers:

                teacher_db_id = teacher[0]
                teacher_id = teacher[1]
                teacher_name = teacher[2]
                teacher_email = teacher[3]
                created_at = teacher[4]

                with st.expander(
                    f"👨‍🏫 {teacher_name} ({teacher_id})"
                ):

                    col1, col2 = st.columns(2)

                    with col1:

                        st.write(
                            f"**Teacher ID:** {teacher_id}"
                        )

                        st.write(
                            f"**Name:** {teacher_name}"
                        )

                        st.write(
                            f"**Email:** {teacher_email}"
                        )

                    with col2:

                        st.write(
                            f"**Database ID:** {teacher_db_id}"
                        )

                        st.write(
                            f"**Created:** {created_at}"
                        )

    # =================================================
    # EDIT TEACHER
    # =================================================

    elif teacher_menu == "Edit Teacher":

        st.write(
            "### ✏️ Edit Teacher"
        )

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        try:

            cursor.execute(
                """
                SELECT
                    id,
                    teacher_id,
                    name,
                    email
                FROM teachers
                ORDER BY name
                """
            )

            teachers = cursor.fetchall()

        except Exception as e:

            conn.close()

            st.error(
                f"Database Error: {e}"
            )

            return

        conn.close()

        if not teachers:

            st.info(
                "No teachers available."
            )

            return

        # =================================================
        # TEACHER SELECTION
        # =================================================

        teacher_options = {
            f"{teacher[2]} ({teacher[1]})":
            teacher[0]
            for teacher in teachers
        }

        selected_teacher = st.selectbox(
            "Select Teacher",
            list(teacher_options.keys()),
            key="edit_teacher_select"
        )

        selected_teacher_db_id = teacher_options[
            selected_teacher
        ]

        # =================================================
        # GET SELECTED TEACHER INFORMATION
        # =================================================

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        try:

            cursor.execute(
                """
                SELECT
                    id,
                    teacher_id,
                    name,
                    email
                FROM teachers
                WHERE id = ?
                """,
                (
                    selected_teacher_db_id,
                )
            )

            teacher = cursor.fetchone()

        except Exception as e:

            conn.close()

            st.error(
                f"Database Error: {e}"
            )

            return

        conn.close()

        if not teacher:

            st.error(
                "Selected teacher information not found."
            )

            return

        # =================================================
        # CURRENT TEACHER DATA
        # =================================================

        current_db_id = teacher[0]
        current_teacher_id = teacher[1] or ""
        current_name = teacher[2] or ""
        current_email = teacher[3] or ""

        # =================================================
        # UNIQUE WIDGET KEYS
        # =================================================
        #
        # IMPORTANT:
        # The selected teacher database ID is included
        # in the widget key so Streamlit does not reuse
        # the previous teacher's values.
        #
        # =================================================

        id_key = f"edit_teacher_id_{current_db_id}"
        name_key = f"edit_teacher_name_{current_db_id}"
        email_key = f"edit_teacher_email_{current_db_id}"
        password_key = f"edit_teacher_password_{current_db_id}"
        update_key = f"update_teacher_button_{current_db_id}"

        # =================================================
        # EDIT FORM
        # =================================================

        new_teacher_id = st.text_input(
            "Teacher ID",
            value=current_teacher_id,
            key=id_key
        )

        new_name = st.text_input(
            "Teacher Name",
            value=current_name,
            key=name_key
        )

        new_email = st.text_input(
            "Teacher Email",
            value=current_email,
            key=email_key
        )

        st.write(
            "### 🔐 Change Password"
        )

        new_password = st.text_input(
            "New Password",
            type="password",
            placeholder="Leave blank to keep current password",
            key=password_key
        )

        # =================================================
        # UPDATE TEACHER
        # =================================================

        if st.button(
            "💾 Update Teacher",
            key=update_key
        ):

            if not new_teacher_id.strip():

                st.error(
                    "Teacher ID cannot be empty."
                )

                return

            if not new_name.strip():

                st.error(
                    "Teacher Name cannot be empty."
                )

                return

            if not new_email.strip():

                st.error(
                    "Teacher Email cannot be empty."
                )

                return

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            try:

                # -----------------------------------------
                # DUPLICATE TEACHER ID
                # -----------------------------------------

                cursor.execute(
                    """
                    SELECT id
                    FROM teachers
                    WHERE teacher_id = ?
                    AND id != ?
                    """,
                    (
                        new_teacher_id.strip(),
                        current_db_id
                    )
                )

                if cursor.fetchone():

                    st.error(
                        "❌ Teacher ID already exists."
                    )

                    return

                # -----------------------------------------
                # DUPLICATE EMAIL
                # -----------------------------------------

                cursor.execute(
                    """
                    SELECT id
                    FROM teachers
                    WHERE LOWER(TRIM(email)) = ?
                    AND id != ?
                    """,
                    (
                        new_email.strip().lower(),
                        current_db_id
                    )
                )

                if cursor.fetchone():

                    st.error(
                        "❌ Teacher Email already exists."
                    )

                    return

                # -----------------------------------------
                # UPDATE WITH NEW PASSWORD
                # -----------------------------------------

                if new_password:

                    cursor.execute(
                        """
                        UPDATE teachers
                        SET
                            teacher_id = ?,
                            name = ?,
                            email = ?,
                            password = ?
                        WHERE id = ?
                        """,
                        (
                            new_teacher_id.strip(),
                            new_name.strip(),
                            new_email.strip(),
                            hash_password(new_password),
                            current_db_id
                        )
                    )

                # -----------------------------------------
                # UPDATE WITHOUT CHANGING PASSWORD
                # -----------------------------------------

                else:

                    cursor.execute(
                        """
                        UPDATE teachers
                        SET
                            teacher_id = ?,
                            name = ?,
                            email = ?
                        WHERE id = ?
                        """,
                        (
                            new_teacher_id.strip(),
                            new_name.strip(),
                            new_email.strip(),
                            current_db_id
                        )
                    )

                conn.commit()

                st.success(
                    f"✅ Teacher '{new_name.strip()}' updated successfully."
                )

                st.rerun()

            except Exception as e:

                conn.rollback()

                st.error(
                    f"Database Error: {e}"
                )

            finally:

                conn.close()

    # =================================================
    # DELETE TEACHER
    # =================================================

    elif teacher_menu == "Delete Teacher":

        st.write(
            "### 🗑️ Delete Teacher"
        )

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                teacher_id,
                name,
                email
            FROM teachers
            ORDER BY name
            """
        )

        teachers = cursor.fetchall()

        conn.close()

        if not teachers:

            st.info(
                "No teachers available."
            )

            return

        teacher_options = {
            f"{teacher[2]} ({teacher[1]})":
            teacher[0]
            for teacher in teachers
        }

        selected_teacher = st.selectbox(
            "Select Teacher",
            list(teacher_options.keys()),
            key="delete_teacher_select"
        )

        selected_teacher_db_id = teacher_options[
            selected_teacher
        ]

        st.warning(
            "⚠️ Deleting a teacher is a permanent action."
        )

        confirm_delete = st.checkbox(
            "I confirm that I want to delete this teacher.",
            key="confirm_delete_teacher"
        )

        if st.button(
            "🗑️ Delete Teacher",
            key="delete_teacher_button"
        ):

            if not confirm_delete:

                st.error(
                    "Please confirm deletion first."
                )

                return

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            try:

                # -----------------------------------------
                # DELETE ASSIGNMENTS FIRST
                # -----------------------------------------

                cursor.execute(
                    """
                    DELETE FROM teacher_student
                    WHERE teacher_id = ?
                    """,
                    (
                        selected_teacher_db_id,
                    )
                )

                # -----------------------------------------
                # DELETE TEACHER
                # -----------------------------------------

                cursor.execute(
                    """
                    DELETE FROM teachers
                    WHERE id = ?
                    """,
                    (
                        selected_teacher_db_id,
                    )
                )

                conn.commit()

                st.success(
                    "✅ Teacher deleted successfully."
                )

                st.rerun()

            except Exception as e:

                conn.rollback()

                st.error(
                    f"Database Error: {e}"
                )

            finally:

                conn.close()
# =====================================================
# VERIFY TEACHER LOGIN
# =====================================================

def verify_teacher_login(email, password):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT
                id,
                teacher_id,
                name,
                email,
                password
            FROM teachers
            WHERE LOWER(TRIM(email)) = ?
            """,
            (
                email.strip().lower(),
            )
        )

        teacher = cursor.fetchone()

        if teacher is None:
            return None

        stored_password = teacher[4]

        hashed_password = hash_password(password)

        if stored_password != hashed_password:
            return None

        return {
            "id": teacher[0],
            "teacher_id": teacher[1],
            "name": teacher[2],
            "email": teacher[3]
        }

    except sqlite3.Error:

        return None

    finally:

        conn.close()