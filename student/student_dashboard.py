import streamlit as st, pandas as pd
from utils.rbac import allow_roles
from utils.models import get_scores, student_enrollments ,attendance_summary,get_recent_notifications
from utils.gpa import current_gpa, projected_gpa
import myCourses,Attendance
from student import gpa



@allow_roles("student")
def main():
    st.set_page_config(page_title="EduShield | 🧑‍🏫 Dashboard", page_icon="images/Edushield_Icon1.png", layout="wide")
    
    st.title("📊 Student Dashboard")
    u = st.session_state["user"]

    st.success(f"👋 Welcome, {u['full_name']}!")
    st.caption("🎓 “Stay on track, stay ahead — your academic journey starts here.”")

    # Session/Semester Selection
    st.markdown("--------------------")
    st.subheader("🔍 Session/Semester Filter")
    col1, col2 = st.columns(2)
    with col1:
        session = st.selectbox("📅 Session", ["2024/2025"])
    with col2:
        semester = st.selectbox("🏫 Semester", ["First", "Second"])
    
    st.markdown("--------------------")

    # --------------------------
    # Quick Stats Section
    # --------------------------
    st.subheader("⚡ Quick Stats")
    scores = get_scores(u["id"])
    cgpa = current_gpa(scores)
    pgpa = projected_gpa(scores)

    col1, col2, col3 = st.columns(3)
    col1.metric("Current GPA", cgpa)
    col2.metric("Projected GPA", pgpa)
    st.markdown("--------------------")
   

    # Attendance Summary (Quick Stat + Table)
    attendance_data = attendance_summary(u["id"])

    if attendance_data:
        df_att = pd.DataFrame(attendance_data)
        avg_att = round(df_att["Attendance %"].mean(), 1)
        st.subheader("Attendance % by Course")
        st.dataframe(df_att, use_container_width=True)
    else:
        avg_att = 0
        # df_att = pd.DataFrame()
        st.subheader("Attendance % by Course")
        st.info("No Attendance found for this session/semester.")


    col3.metric("Attendance %", f"{avg_att}%")
    
    st.markdown("--------------------")


    # --------------------------
    # Enrollment Summary
    # --------------------------
    st.subheader("📚 My Enrollments")
    enrolls = student_enrollments(u["id"], session, semester)
    if enrolls:
        st.dataframe(pd.DataFrame(enrolls))
    else:
        st.info("No enrollments found for this session/semester.")
     

    # --------------------------
    # Notifications Preview
    # --------------------------

    st.markdown("--------------------")
    st.subheader("🔔 Notifications")

    notifications = get_recent_notifications(u["id"], limit=3)

    if notifications:
        for note in notifications:
            st.markdown(
                f"- **{note['title']}**  \n"
                f"  {note['message']}  _(📅 {note['created_at']})_"
            )
    else:
        st.info("No new notifications.")

    st.markdown("--------------------")

    # --------------------------
    # Shortcuts Section
    # --------------------------
    st.subheader("🚀 Quick Actions")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📖 View Courses"):
            myCourses.main()
    with col2:
        if st.button("📝 Attendance"):
            Attendance.main()
    with col3:
        if st.button("🎓 GPA Details"):
            gpa.main()
    
    st.markdown("---------------")


if __name__ == "__main__":
    main()
