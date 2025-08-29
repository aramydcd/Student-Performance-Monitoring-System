import streamlit as st, pandas as pd
from utils.rbac import allow_roles
from utils.models import get_scores, student_enrollments, percentage_attendance ,attendance_summary, get_attendance
from utils.gpa import current_gpa, projected_gpa

@allow_roles("student")
def main():
    st.title("📊 Student Dashboard")
    u = st.session_state["user"]
    session = st.selectbox("Session", ["2024/2025"])
    semester = st.selectbox("Semester", ["First","Second"])
    enrolls = student_enrollments(u["id"], session, semester)
     
    st.subheader("Enrollments")
    st.dataframe(pd.DataFrame(enrolls))


    scores = get_scores(u["id"])
    st.subheader("Scores")
    st.dataframe(pd.DataFrame(scores))


    # GPA Section
    cgpa = current_gpa(scores)
    pgpa = projected_gpa(scores)
    st.metric("Current GPA", cgpa)
    st.metric("Projected GPA", pgpa)

    # Attendance Summary
    st.subheader("Attendance % by Course")
    attendance_pct = attendance_summary(u["id"])
    st.dataframe(pd.DataFrame(attendance_pct))

    # Detailed Records
    st.subheader("Attendance Records")
    attendance = get_attendance(u["id"])
    st.dataframe(pd.DataFrame(attendance))


if __name__ == "__main__":
    main()
