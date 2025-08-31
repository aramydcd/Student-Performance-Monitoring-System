import streamlit as st, pandas as pd
from utils.rbac import allow_roles
from utils.models import lecturer_pick_course, list_students_in_course
from utils.db import get_conn

@allow_roles("lecturer")
def main():
    st.title("👩🏽‍🏫 Lecturer Portal")
    st.success("🧑‍🏫 Welcome to the Lecturer Dashboard!")

    u = st.session_state["user"]
    session = st.selectbox("Session", ["2024/2025"])
    semester = st.selectbox("Semester", ["First","Second"])
    with get_conn() as conn:
        courses = conn.execute("SELECT id, code, title FROM courses WHERE is_active=1 ORDER BY code").fetchall()
    course_map = {f"{c['code']} - {c['title']}": c["id"] for c in courses}
    course_label = st.selectbox("Select a course to teach", list(course_map.keys()))
    if st.button("Add to my courses"):
        lecturer_pick_course(u["id"], course_map[course_label], session, semester)
        st.success("Course added.")
    with get_conn() as conn:
        mine = conn.execute("""
          SELECT lc.id, c.code, c.title FROM lecturer_courses lc
          JOIN courses c ON c.id=lc.course_id
          WHERE lc.lecturer_id=? AND lc.session=? AND lc.semester=?
          ORDER BY c.code
        """,(u["id"],session,semester)).fetchall()
    st.subheader("My Courses")
    st.dataframe(pd.DataFrame(mine))
    if mine:
        pick = st.selectbox("Open course", [f"{m['code']} - {m['title']}" for m in mine])
        cid = [m["id"] for m in mine if f"{m['code']} - {m['title']}"==pick][0]
        # show students
        with get_conn() as conn:
            course_id = conn.execute("SELECT course_id FROM lecturer_courses WHERE id=?", (cid,)).fetchone()["course_id"]
        st.subheader("Enrolled Students")
        st.dataframe(pd.DataFrame(list_students_in_course(course_id, session, semester)))

if __name__ == "__main__":
    main()
