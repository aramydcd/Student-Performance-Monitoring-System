import streamlit as st
import pandas as pd
from utils.rbac import allow_roles
from utils.models import lecturer_pick_course, list_students_in_course, get_recent_notifications,get_course_id_by_code
from utils.db import get_conn

@allow_roles("lecturer")
def main():
    st.set_page_config(page_title="EduShield | 👩🏽‍🏫 Dashboard", page_icon="images/Edushield_Icon1.png", layout="wide")

    st.title("👩🏽‍🏫 Lecturer Portal")
    u = st.session_state["user"]

    st.success(f"🧑‍🏫 Welcome, {u['full_name']}!")
    st.caption("📘 “Empower learning, inspire minds — manage your courses with ease.”")

    # -------------------------------
    # Session/Semester Selection
    # -------------------------------
    st.markdown("--------------------")
    st.subheader("🔍 Session/Semester Filter")
    col1, col2 = st.columns(2)
    with col1:
        session = st.selectbox("📅 Session", ["2024/2025"])
    with col2:
        semester = st.selectbox("🏫 Semester", ["First", "Second"])

    st.divider()

    # -------------------------------
    # Fetch lecturer's current courses
    # -------------------------------
    st.subheader("✍️ Register Course")
    with get_conn() as conn:
        mine = conn.execute("""
            SELECT c.code, c.title, c.units
            FROM lecturer_courses lc
            JOIN courses c ON c.id=lc.course_id
            WHERE lc.lecturer_id=? AND lc.session=? AND lc.semester=?
            ORDER BY c.code
        """,(u["id"], session, semester)).fetchall()

    my_course_ids = [m["code"] for m in mine]  # already registered

    # -------------------------------
    # Add Courses to Teach
    # -------------------------------
    with get_conn() as conn:
        courses = conn.execute(
            "SELECT id, code, title FROM courses WHERE is_active=1 ORDER BY code"
        ).fetchall()

    # Filter out already-registered courses
    available_courses = [c for c in courses if c["code"] not in my_course_ids]

    if available_courses:
        course_map = {f"{c['code']} - {c['title']}": c["id"] for c in available_courses}
        course_label = st.selectbox("Select a course to teach", list(course_map.keys()))
        if st.button("➕ Add to my courses"):
            lecturer_pick_course(u["id"], course_map[course_label], session, semester)
            st.success("✅ Course added.")
    else:
        st.info("🎉 You’ve already registered all available courses for this semester.")

    # -------------------------------
    # Course Summary
    # -------------------------------
    st.divider()
    st.subheader("📊 My Courses Summary")

    if mine:
        df_courses = pd.DataFrame(mine, columns=["Course Code", "Course Title", "Course Units"])
        # # print(mine)
        # df_courses = df_courses.rename(columns={
        #     "id": "Record ID",
        #     "code": "Course Code",
        #     "title": "Course Title"
        # })
        st.metric("Total Courses", len(df_courses))
        st.dataframe(df_courses, use_container_width=True)

        # st.dataframe(df_courses, use_container_width=True)
    else:
        st.info("You have not registered for any courses this semester.")

    # -------------------------------
    # Quick Attendance / Assessment Overview
    # -------------------------------
    st.divider()
    st.subheader("📝 Quick Overview")

    if mine:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Average Attendance", "82%")  # Placeholder
        with col2:
            st.metric("Assessment Submissions", "120")  # Placeholder
        st.caption("ℹ️ Detailed analytics will appear here once attendance/assessments are implemented.")
    else:
        st.info("No overview available. Register for courses to see stats.")

    # -------------------------------
    # Notifications
    # -------------------------------
    st.divider()
    st.subheader("🔔 Notifications")

    notes = get_recent_notifications(u["id"], limit=3)
    if notes:
        for note in notes:
            st.markdown(
                f"- **{note['title']}**  \n"
                f"  {note['message']}  _(📅 {note['created_at']})_"
            )
    else:
        st.info("No new notifications.")

    # -------------------------------
    # Open Course → Show Students
    # -------------------------------
    st.divider()
    st.subheader("👥 Manage Course")
 
    if mine:
        pick = st.selectbox("Open course", [f"{m['code']} - {m['title']}" for m in mine])
        course_code = [m["code"] for m in mine if f"{m['code']} - {m['title']}" == pick][0]

        cid = get_course_id_by_code(course_code)

        st.subheader("📚 Enrolled Students")
        course_list = list_students_in_course(cid, session, semester)
        if course_list:
            st.dataframe(pd.DataFrame(course_list,columns=["Student Name","Email"]), use_container_width=True)
        else:
            st.info(f"No Student have enrolled for {course_code} yet.")

    st.divider()


if __name__ == "__main__":
    main()

