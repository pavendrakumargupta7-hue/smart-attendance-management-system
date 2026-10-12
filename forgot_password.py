import streamlit as st
import sqlite3
import hashlib
import secrets
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta


# ============================================================
# DATABASE
# ============================================================

BASE_DIR = __import__("os").path.dirname(__file__)
DB_PATH = __import__("os").path.join(BASE_DIR, "students.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# PASSWORD HASHING
# Same SHA-256 method used by teacher_management.py
# ============================================================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ============================================================
# OTP HELPERS
# ============================================================

def generate_otp():
    return str(secrets.randbelow(900000) + 100000)


def send_otp_email(receiver_email, otp):
    sender_email = st.secrets["GMAIL_EMAIL"]
    app_password = st.secrets["GMAIL_APP_PASSWORD"]

    msg = EmailMessage()

    msg["Subject"] = "SAMS Teacher Password Reset OTP"
    msg["From"] = sender_email
    msg["To"] = receiver_email

    msg.set_content(
        f"""
Smart Attendance Management System (SAMS)

Your password reset OTP is:

{otp}

This OTP is valid for 10 minutes.

If you did not request a password reset, please ignore this email.

Regards,
SAMS Administration
"""
    )

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, app_password)
        server.send_message(msg)


# ============================================================
# FIND TEACHER
# ============================================================

def get_teacher_by_email(email):
    conn = get_db_connection()

    try:
        teacher = conn.execute(
            """
            SELECT id, teacher_id, name, email
            FROM teachers
            WHERE LOWER(TRIM(email)) = ?
            """,
            (email.strip().lower(),)
        ).fetchone()

        return teacher

    finally:
        conn.close()


# ============================================================
# UPDATE TEACHER PASSWORD
# ============================================================

def update_teacher_password(teacher_id, new_password):
    conn = get_db_connection()

    try:
        hashed_password = hash_password(new_password)

        conn.execute(
            """
            UPDATE teachers
            SET password = ?
            WHERE id = ?
            """,
            (hashed_password, teacher_id)
        )

        conn.commit()

    finally:
        conn.close()


# ============================================================
# FORGOT PASSWORD PAGE
# ============================================================

def forgot_password():

    st.subheader("🔐 Forgot Teacher Password")

    # --------------------------------------------------------
    # INITIAL SESSION STATE
    # --------------------------------------------------------

    if "forgot_password_step" not in st.session_state:
        st.session_state.forgot_password_step = 1

    if "forgot_password_teacher" not in st.session_state:
        st.session_state.forgot_password_teacher = None

    if "forgot_password_otp" not in st.session_state:
        st.session_state.forgot_password_otp = None

    if "forgot_password_otp_expiry" not in st.session_state:
        st.session_state.forgot_password_otp_expiry = None

    # ========================================================
    # STEP 1 — ENTER EMAIL
    # ========================================================

    if st.session_state.forgot_password_step == 1:

        st.info(
            "Enter the email address registered with your teacher account."
        )

        email = st.text_input(
            "Teacher Email",
            key="forgot_teacher_email"
        )

        if st.button(
            "Send OTP",
            type="primary",
            key="send_teacher_otp"
        ):

            email = email.strip().lower()

            if not email:
                st.warning("Please enter your registered email.")
                return

            teacher = get_teacher_by_email(email)

            if not teacher:
                st.error(
                    "No teacher account was found with this email."
                )
                return

            otp = generate_otp()

            try:
                send_otp_email(email, otp)

                st.session_state.forgot_password_teacher = dict(teacher)
                st.session_state.forgot_password_otp = otp
                st.session_state.forgot_password_otp_expiry = (
                    datetime.now() + timedelta(minutes=10)
                )
                st.session_state.forgot_password_step = 2

                st.success(
                    "✅ OTP has been sent to your registered email."
                )

                st.rerun()

            except Exception as e:
                st.error(
                    "❌ Failed to send OTP email."
                )

                st.caption(
                    f"Email error: {str(e)}"
                )

    # ========================================================
    # STEP 2 — VERIFY OTP
    # ========================================================

    elif st.session_state.forgot_password_step == 2:

        teacher = st.session_state.forgot_password_teacher

        if not teacher:
            st.session_state.forgot_password_step = 1
            st.rerun()

        st.info(
            f"OTP sent to: {teacher['email']}"
        )

        otp_input = st.text_input(
            "Enter 6-digit OTP",
            max_chars=6,
            key="teacher_otp_input"
        )

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                "Verify OTP",
                type="primary",
                key="verify_teacher_otp"
            ):

                current_time = datetime.now()
                expiry = st.session_state.forgot_password_otp_expiry

                if not expiry:
                    st.error("OTP session expired. Please request a new OTP.")
                    return

                if current_time > expiry:
                    st.error(
                        "❌ OTP has expired. Please request a new OTP."
                    )

                    st.session_state.forgot_password_otp = None
                    st.session_state.forgot_password_step = 1

                    return

                if otp_input.strip() != str(
                    st.session_state.forgot_password_otp
                ):
                    st.error("❌ Invalid OTP.")
                    return

                st.session_state.forgot_password_step = 3

                st.success("✅ OTP verified successfully.")

                st.rerun()

        with col2:

            if st.button(
                "Resend OTP",
                key="resend_teacher_otp"
            ):

                new_otp = generate_otp()

                try:
                    send_otp_email(
                        teacher["email"],
                        new_otp
                    )

                    st.session_state.forgot_password_otp = new_otp
                    st.session_state.forgot_password_otp_expiry = (
                        datetime.now() + timedelta(minutes=10)
                    )

                    st.success(
                        "✅ New OTP sent successfully."
                    )

                except Exception as e:
                    st.error(
                        "❌ Failed to resend OTP."
                    )

                    st.caption(
                        f"Email error: {str(e)}"
                    )

    # ========================================================
    # STEP 3 — NEW PASSWORD
    # ========================================================

    elif st.session_state.forgot_password_step == 3:

        teacher = st.session_state.forgot_password_teacher

        if not teacher:
            st.session_state.forgot_password_step = 1
            st.rerun()

        st.success("✅ OTP verified.")

        st.write(
            f"Teacher: **{teacher['name']}**"
        )

        new_password = st.text_input(
            "New Password",
            type="password",
            key="new_teacher_password"
        )

        confirm_password = st.text_input(
            "Confirm New Password",
            type="password",
            key="confirm_teacher_password"
        )

        if st.button(
            "Update Password",
            type="primary",
            key="update_teacher_password"
        ):

            if not new_password or not confirm_password:
                st.warning(
                    "Please enter and confirm your new password."
                )
                return

            if len(new_password) < 6:
                st.warning(
                    "Password must contain at least 6 characters."
                )
                return

            if new_password != confirm_password:
                st.error(
                    "❌ Passwords do not match."
                )
                return

            update_teacher_password(
                teacher["id"],
                new_password
            )

            # Clear reset session
            st.session_state.forgot_password_step = 1
            st.session_state.forgot_password_teacher = None
            st.session_state.forgot_password_otp = None
            st.session_state.forgot_password_otp_expiry = None

            st.success(
                "✅ Password updated successfully."
            )

            st.info(
                "You can now login using your new password."
            )

if __name__ == "__main__":
    forgot_password()