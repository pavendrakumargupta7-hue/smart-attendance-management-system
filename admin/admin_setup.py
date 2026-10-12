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
# ADMIN SETUP
# =====================================================

def admin_setup():

    st.title("⚙️ Admin Setup")

    st.write(
        "Create the main administrator account."
    )

    # =================================================
    # ADMIN DETAILS
    # =================================================

    admin_id = st.text_input(
        "Admin ID",
        placeholder="Enter Admin ID",
        key="setup_admin_id"
    )

    admin_name = st.text_input(
        "Admin Name",
        placeholder="Enter Admin Name",
        key="setup_admin_name"
    )

    admin_email = st.text_input(
        "Admin Email",
        placeholder="Enter Admin Email",
        key="setup_admin_email"
    )

    password = st.text_input(
        "Password",
        type="password",
        key="setup_admin_password"
    )

    confirm_password = st.text_input(
        "Confirm Password",
        type="password",
        key="setup_admin_confirm_password"
    )

    # =================================================
    # CREATE ADMIN
    # =================================================

    if st.button(
        "Create Admin",
        key="create_admin_button"
    ):

        if not admin_id.strip():

            st.error(
                "Please enter Admin ID."
            )
            return

        if not admin_name.strip():

            st.error(
                "Please enter Admin Name."
            )
            return

        if not admin_email.strip():

            st.error(
                "Please enter Admin Email."
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

        # =============================================
        # DATABASE CONNECTION
        # =============================================

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # =============================================
        # CREATE ADMINS TABLE IF NOT EXISTS
        # =============================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # =============================================
        # INSERT ADMIN
        # =============================================

        try:

            cursor.execute(
                """
                INSERT INTO admins
                (
                    admin_id,
                    name,
                    email,
                    password
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    admin_id.strip(),
                    admin_name.strip(),
                    admin_email.strip(),
                    hash_password(password)
                )
            )

            conn.commit()

            st.success(
                "✅ Admin account created successfully."
            )

            st.info(
                "Now go to Admin → Admin Login and use the same Admin ID and Password."
            )

        except sqlite3.IntegrityError:

            st.error(
                "❌ Admin ID or Email already exists."
            )

        finally:

            conn.close()