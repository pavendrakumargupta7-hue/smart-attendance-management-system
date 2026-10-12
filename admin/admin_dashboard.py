
import streamlit as st

from admin.teacher_management import teacher_management
from admin.student_management import student_management
from admin.attendance_management import attendance_management


def admin_dashboard():

    # =====================================================
    # ADMIN LOGIN CHECK
    # =====================================================

    if not st.session_state.get(
        "admin_logged_in",
        False
    ):
        st.warning("🔒 Please login as Admin first.")
        return

    # =====================================================
    # ADMIN DASHBOARD HEADER
    # =====================================================

    st.title("👑 Admin Dashboard")

    admin_name = st.session_state.get(
        "admin_name",
        "Admin"
    )

    st.success(
        f"Welcome, {admin_name}!"
    )

    st.write("---")

    # =====================================================
    # ADMIN MENU
    # =====================================================

    admin_menu = st.selectbox(
        "Admin Menu",
        [
            "Dashboard",
            "Teacher Management",
            "Student Management",
            "Attendance Management"
        ],
        key="admin_dashboard_menu"
    )

    # =====================================================
    # DASHBOARD
    # =====================================================

    if admin_menu == "Dashboard":

        st.subheader("📊 Admin Dashboard")

        st.write(
            "Welcome to the Smart Attendance Management System Admin Panel."
        )

        st.write("---")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "👨‍🎓 Students",
                "—"
            )

        with col2:
            st.metric(
                "👨‍🏫 Teachers",
                "—"
            )

        with col3:
            st.metric(
                "📋 Attendance",
                "—"
            )

    # =====================================================
    # TEACHER MANAGEMENT
    # =====================================================

    elif admin_menu == "Teacher Management":

        teacher_management()

    # =====================================================
    # STUDENT MANAGEMENT
    # =====================================================

    elif admin_menu == "Student Management":

        student_management()

    # =====================================================
    # ATTENDANCE MANAGEMENT
    # =====================================================

    elif admin_menu == "Attendance Management":

        attendance_management()
