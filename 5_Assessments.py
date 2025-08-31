import streamlit as st, pandas as pd
from utils.rbac import allow_roles
from utils.models import list_students_in_course, upsert_score, get_scores
from utils.db import get_conn

@allow_roles("lecturer","student")
def main():
    st.title("📝 Assessments")
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
        component = st.selectbox("Component", ["test","assignment","exam"])
        students = list_students_in_course(chosen["course_id"], session, semester)
        st.subheader("Enter Scores")
        for s in students:
            score = st.number_input(f"{s['full_name']}", 0.0, 100.0, 0.0, step=1.0, key=f"sc_{s['id']}")
            if st.button(f"Save {s['full_name']}", key=f"save_sc_{s['id']}"):
                upsert_score(chosen["course_id"], s["id"], component, score, u["id"])
                st.success("Saved.")
    else:
        # students will view scores in dashboard

        st.markdown("--------------------")

        scores = get_scores(u["id"])
        st.subheader("Assessments & Assignment Scores")
        if scores:
            st.dataframe(pd.DataFrame(scores))
        else:
            st.info("No Assessments/Assignment score recorded yet!.")



if __name__ == "__main__":
    main()
