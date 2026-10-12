import streamlit as st

from admin.teacher_management import verify_teacher_login
from teacher_dashboard import teacher_dashboard


# =====================================================
# TEACHER LOGIN
# =====================================================

def teacher_login():

    # -------------------------------------------------
    # ALREADY LOGGED IN
    # -------------------------------------------------

    if (
        st.session_state.get("teacher_logged_in", False)
        and st.session_state.get("teacher")
    ):

        teacher_dashboard()

        return

    # -------------------------------------------------
    # LOGIN UI
    # -------------------------------------------------

    st.subheader("👨‍🏫 Teacher Login")

    email = st.text_input(
        "Teacher Email",
        key="teacher_login_email"
    )

    password = st.text_input(
        "Teacher Password",
        type="password",
        key="teacher_login_password"
    )

    # -------------------------------------------------
    # LOGIN BUTTON
    # -------------------------------------------------

    if st.button(
        "Teacher Login",
        type="primary",
        key="teacher_login_button"
    ):

        if not email or not password:

            st.warning(
                "Please enter email and password."
            )

            return

        # -------------------------------------------------
        # VERIFY TEACHER
        # -------------------------------------------------

        teacher = verify_teacher_login(
            email,
            password
        )

        if teacher:

            # ---------------------------------------------
            # SAVE CURRENT TEACHER SESSION
            # ---------------------------------------------

            st.session_state.teacher_logged_in = True

            # IMPORTANT:
            # This is the logged-in teacher's database ID.
            # All teacher-specific data will use this ID.

            st.session_state.teacher_id = teacher["id"]

            st.session_state.teacher_name = teacher["name"]

            st.session_state.teacher = teacher

            st.session_state.teacher_menu = "Dashboard"

            st.success(
                f"✅ Welcome {teacher['name']} Sir!"
            )

            st.rerun()

        else:

            st.error(
                "❌ Invalid Email or Password"
            )


# =====================================================
# TEACHER LOGOUT
# =====================================================

def teacher_logout():

    st.session_state.teacher_logged_in = False

    st.session_state.teacher_id = None

    st.session_state.teacher_name = ""

    st.session_state.teacher = None

    st.session_state.teacher_menu = "Dashboard"

    st.rerun()