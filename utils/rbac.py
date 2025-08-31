import streamlit as st

def require_login():
    if "user" not in st.session_state:
        st.switch_page("app.py")

def allow_roles(*roles):
    def deco(func):
        def wrapper(*args, **kwargs):
            require_login()
            if st.session_state["user"]["role"] not in roles:
                st.error("You do not have permission to view this page.")
                return
            return func(*args, **kwargs)
        return wrapper
    return deco

def menu_for_role(role:str):
    # Pages are already split; this helper can show contextual hints
    if role == "student":
        return ["Student_Dashboard","Attendance","Assessments","Course_Registration","Group_Messaging"]
    if role == "lecturer":
        return ["Lecturer_Portal","Attendance","Assessments","Group_Messaging"]
    if role == "admin":
        return ["Admin_Panel","Course_Registration"]
    return []
