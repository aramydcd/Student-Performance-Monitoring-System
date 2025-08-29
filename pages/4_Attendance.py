import streamlit as st, pandas as pd, datetime
from utils.rbac import allow_roles
from utils.models import list_students_in_course, mark_attendance
from utils.db import get_conn

@allow_roles("lecturer","student")
def main():
    st.title("🗓️ Attendance")
    u = st.session_state["user"]
    session = st.selectbox("Session", ["2024/2025"])
    semester = st.selectbox("Semester", ["First","Second"])

    if u["role"]=="lecturer":
        with get_conn() as conn:
            mine = conn.execute("""SELECT lc.id, c.id AS course_id, c.code, c.title
                                   FROM lecturer_courses lc JOIN courses c ON c.id=lc.course_id
                                   WHERE lc.lecturer_id=? AND lc.session=? AND lc.semester=?
                                   ORDER BY c.code""",(u["id"],session,semester)).fetchall()
        if not mine:
            st.info("Add courses in Lecturer Portal first.")
            return
        label = st.selectbox("Course", [f"{m['code']} - {m['title']}" for m in mine])
        chosen = [m for m in mine if f"{m['code']} - {m['title']}"==label][0]
        class_date = st.date_input("Class Date", datetime.date.today()).isoformat()
        students = list_students_in_course(chosen["course_id"], session, semester)
        st.write("Mark presence:")
        for s in students:
            present = st.checkbox(s["full_name"], value=True, key=f"att_{s['id']}")
            if st.button(f"Save {s['full_name']}", key=f"save_{s['id']}"):
                mark_attendance(chosen["course_id"], s["id"], class_date, present, u["id"])
                st.success("Saved.")
    else:
        st.info("Students can view attendance percentage in Dashboard.")

if __name__ == "__main__":
    main()
