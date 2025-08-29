import streamlit as st, pandas as pd
from utils.rbac import allow_roles
from utils.models import list_courses_for_level, enroll_student, student_enrollments

@allow_roles("student","admin")
def main():
    st.title("🧾 Course Registration")
    u = st.session_state["user"]
    session = st.selectbox("Session", ["2024/2025"])
    semester = st.selectbox("Semester", ["First","Second"])
    if u["role"]=="student":
        level = u["level"] or "ND1"
        st.caption(f"Level: {level}")
        courses = list_courses_for_level(level)
        picks = st.multiselect("Select courses", [f"{c['code']} - {c['title']} ({c['units']}u)" for c in courses])
        if st.button("Register"):
            ids = [c["id"] for c in courses if f"{c['code']} - {c['title']} ({c['units']}u)" in picks]
            for cid in ids:
                enroll_student(u["id"], cid, session, semester)
            st.success("Registration saved.")
        st.subheader("My registrations")
        st.dataframe(pd.DataFrame(student_enrollments(u["id"], session, semester)))
    else:
        st.write("Admins can register students by impersonation (future enhancement).")

if __name__ == "__main__":
    main()
