import streamlit as st
import sqlite3, bcrypt, re
from utils.models import create_user,get_user_by_email,update_is_active,get_user_by_matric
from utils.db import get_conn



def set_user_session(user_row):
    """Set the session state for a logged-in user."""
    st.session_state['user'] = {
        'id': user_row[0],
        'email': user_row[1],
        'full_name': user_row[2],
        'matric_no': user_row[3],
        'role': user_row[4],
        'level': user_row[6]
    }


# ----------------- AUTHENTICATION -----------------
def sign_in():
    st.subheader("Login")
    email = st.text_input("Email", "admin@example.com")
    password = st.text_input("Password", "123456", type="password")

    if st.button("Sign In"):
        if len(password) < 6:
            st.error("Password must be at least 6 characters long.")
            return
        user = get_user_by_email(email)
        if not user:
            st.error("Email not registered. Please sign up first.")
            return
        hashed_password = user[5]
        if bcrypt.checkpw(password.encode(), hashed_password):
            set_user_session(user)
            update_is_active(user[0], 1)
            st.success(f"Welcome back, {user[2]}!")
            st.rerun()
        else:
            st.error("Incorrect password.")
def sign_up():
    st.subheader("Create a New Account")
    full_name = st.text_input("👤 Full Name", key="signup_full_name")
    col1, col2 = st.columns(2)
    email = col1.text_input("📧 Email", key="signup_email")
    role_display = col2.selectbox("🛠️ Role", ["Student", "Lecturer", "Admin"], key="signup_role")

    role = role_display.lower()  # normalize for DB

    if role == "student":
        matric_no = col1.text_input("Matric Number", key="signup_matric")
        level_options = ["ND1", "ND2", "HND1", "HND2"]
        level = col2.selectbox("🎓 Level", level_options, key="signup_level")
    else:
        matric_no = None
        level = None

    pwd = col1.text_input("🔑 Create Password", type="password")
    con_pwd = col2.text_input("🔑 Confirm Password", type="password")

    if st.button("➕ Create User"):
        if not email or not full_name or not role or not pwd:
            st.error("⚠️ Please fill all required fields.")
            return
        elif len(pwd) < 6:
            st.error("🔑 Password must be at least 6 characters.")
            return
        elif pwd != con_pwd:
            st.error("🚨 Password does not match")
            return
        elif get_user_by_email(email):
            st.error("🚨 Email already exists")
            return
        elif role == "student":
            if not matric_no:
                st.error("🚨 Please, provide matric number")
                return
            if get_user_by_matric(matric_no):
                st.error("🚨 Matric number already exists")
                return
        # ✅ Now handle creation for both students & staff
        hashed = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt())
        user_id = create_user(full_name, email, role, hashed, matric_no, level)
        st.success(f"✅ {role_display} created for {full_name}")

        user_row = get_user_by_email(email)
        set_user_session(user_row)
        update_is_active(user_id, 1)
        st.success("Registration successful!")
        st.rerun()


def reset_password():
    st.subheader("Reset Password")
    email = st.text_input("📧 Registered Email", key="reset_email")
    new_password = st.text_input("🔑 New Password", type="password", key="reset_new")
    confirm_new = st.text_input("🔑 Confirm New Password", type="password", key="reset_confirm")

    if st.button("🔄 Reset Password"):
        if len(new_password) < 6:
            st.error("Password must be at least 6 characters.")
            return
        if new_password != confirm_new:
            st.error("❌ Passwords do not match!")
            return
        user = get_user_by_email(email)
        if not user:
            st.error("⚠️ Email not registered.")
            return
        hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
        with get_conn() as conn:
            c = conn.cursor()
            c.execute("UPDATE users SET password_hash = ? WHERE email = ?", (hashed, email))
            conn.commit()
        st.success("🔄 Password reset successfully!")

def logout():
    if "user" in st.session_state:
        user_id = st.session_state["user"]["id"]
        update_is_active(user_id, 0)
        st.session_state.clear()
        st.success("You have been logged out.")
        st.rerun()
    else:
        st.info("No user is currently logged in.")

def auth():
    if "user" not in st.session_state: # ❌ Not logged in
        st.title("🔐 Authentication")
        tabs = st.tabs(["Sign In", "Sign Up", "Reset Password"])
        with tabs[0]:
            sign_in()
        with tabs[1]:
            sign_up()
        with tabs[2]:
            reset_password()


# ----------------- SIDEBAR -----------------
def sidebar():
    if "user" in st.session_state:
        user = st.session_state["user"]
        st.markdown("### 🧑‍🦰 User Info")
        st.write(f"**Name:** {user['full_name']}")
        st.write(f"**Role:** {user['role'].capitalize()}")
        if user['role'].title() == "Student":
            st.write(f"🎓 Matric No: {user['matric_no']}")
            st.write(f"📖 Level: {user['level']}")
        st.markdown("---")
    else:
        st.info("Not logged in.")

# ----------------- MENU BAR -----------------
def menu():
    role = None
    if "user" in st.session_state:
        user = st.session_state["user"]
        role = user['role'].title()

    # -----------------Account Pages -----------------
    profile_page = st.Page("Profile.py", title="Profile", icon="👤")
    settings = st.Page("settings.py", title="Settings", icon=":material/settings:")
    about_page = st.Page("About_Us.py", title="About Us",icon="ℹ️")
    help_page = st.Page("Help.py", title="Help & Support", icon="🆘")
    logout_page = st.Page(logout, title="Log out", icon=":material/logout:")
    notification_page = st.Page("Notifications.py", title="Notifications", icon="🔔")
    security_settings = st.Page("settings.py", title="Security Settings", icon="🔐")

    myCourses_page = st.Page("myCourses.py", title="My Courses & Resources", icon="📚")

    account_pages = [profile_page,settings,about_page, help_page,logout_page]
    student_pages = []
    lecturer_pages = []
    admin_pages = []

    if role == "Admin":
        account_pages.remove(settings)
        account_pages.insert(1,security_settings)

    # ------------------ Dashboard Pages ---------------------------
    student_dash = st.Page(
        "student/student_dashboard.py",
        title="Dashboard",
        icon="🧑‍🎓",
        default=(role == "Student"),
    )
    lecturer_dash = st.Page(
        "lecturer/lecturer_dashboard.py",
        title="Dashboard",
        icon="👩🏽‍🏫",
        default=(role == "Lecturer"),
    )
    admin_dash = st.Page(
        "admin/admin_dashboard.py",
        title="Dashboard",
        icon="🛡️",
        default=(role == "Admin"),
    )
    

    # ------------------ STUDENTS SPECIAL MENU ---------------------------
    if role == "Student":
        attendance_page = st.Page("Attendance.py", title="Attendance Management", icon="📅")
        assessment_page = st.Page("5_Assessments.py", title="Assessments & Assignments", icon="📝")
        courseReg_page = st.Page("6_Course_Registration.py", title="Course Registration", icon="🧾")
        groupMsg_page = st.Page("7_Group_Messaging.py", title="Group Messaging", icon="💬")

        student_pages = [student_dash,attendance_page,assessment_page,courseReg_page,myCourses_page,notification_page,groupMsg_page]

    # ------------------ Lecturer SPECIAL MENU ---------------------------
    if role == "Lecturer":
        attendance_page = st.Page("Attendance.py", title="Attendance Records", icon="📅")
        assessment_page = st.Page("5_Assessments.py", title="Assessments Management", icon="📝")
        courseReg_page = st.Page("6_Course_Registration.py", title="Course Management", icon="📖")
        groupMsg_page = st.Page("7_Group_Messaging.py", title="Messaging/Announcements", icon="📢")
        student_performance_page = st.Page("lecturer/Student_Performance.py", title="Student Performance", icon="📊")

        lecturer_pages = [lecturer_dash,courseReg_page,myCourses_page,attendance_page,assessment_page,student_performance_page,groupMsg_page,notification_page]


    # ------------------ Admin SPECIAL MENU ---------------------------
    if role == "Admin":
        user_management_page = st.Page("admin/user_management.py", title="User Management",icon="👥")
        courseAllocation_page = st.Page("myCourses.py", title="Course Management", icon="📚")
        report_page = st.Page("admin/report.py", title="Reports & Analytics",icon="📊")
        systemLogs_page = st.Page("admin/System_Logs.py", title="System Logs",icon="🗂️")

        admin_pages = [admin_dash,user_management_page,courseAllocation_page,report_page,systemLogs_page,notification_page]

    # ----------------- Navigation -----------------
    st.set_page_config(page_title="EduShield | 🔐 Authentication", page_icon="images/Edushield_Icon1.png", layout="centered")
    # st.image("images/Edushield_Logo7.png", width=180)
    st.logo("images/Edushield_Logo7.png", icon_image="images/Edushield_Logo7.png")
    
    
   
   # ✅ Order: Dashboard first, Account after
    page_dict = {}
    if role in ["Student", "Admin"]:
        page_dict["General"] = student_pages
        # page_dict[""] = general_pages
    if role in ["Lecturer", "Admin"]:
        page_dict["General"]= lecturer_pages
        # page_dict[""] = general_pages
    if role == "Admin":
        page_dict["General"] = admin_pages

    if len(page_dict) > 0:
        pg = st.navigation(page_dict | {"Account": account_pages})
    else:
        pg = st.navigation([st.Page(auth)])

    pg.run()

# ----------------- MAIN -----------------
def main():
    menu()
    


if __name__ == "__main__":
    main()

