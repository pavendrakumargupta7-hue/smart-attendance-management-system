
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
# ADMIN LOGIN
# =====================================================

def admin_login():

    st.title("🔐 Admin Login")

    admin_id = st.text_input(
        "Admin ID",
        key="admin_login_id"
    )

    password = st.text_input(
        "Password",
        type="password",
        key="admin_login_password"
    )

    if st.button(
        "Login",
        key="admin_login_button"
    ):

        # =================================================
        # VALIDATION
        # =================================================

        if not admin_id.strip():

            st.error(
                "Please enter Admin ID."
            )
            return

        if not password:

            st.error(
                "Please enter Password."
            )
            return

        # =================================================
        # DATABASE CONNECTION
        # =================================================

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # =================================================
        # CHECK ADMIN
        # =================================================

        cursor.execute(
            """
            SELECT
                id,
                admin_id,
                name,
                email
            FROM admins
            WHERE admin_id = ?
            AND password = ?
            """,
            (
                admin_id.strip(),
                hash_password(password)
            )
        )

        admin = cursor.fetchone()

        conn.close()

        # =================================================
        # LOGIN SUCCESS
        # =================================================

        if admin:

            st.session_state["admin_logged_in"] = True
            st.session_state["admin_id"] = admin[0]
            st.session_state["admin_name"] = admin[2]
            st.session_state["admin_email"] = admin[3]

            st.success(
                f"Welcome, {admin[2]}!"
            )

            st.rerun()

        # =================================================
        # LOGIN FAILED
        # =================================================

        else:

            st.error(
                "❌ Invalid Admin ID or Password."
            )