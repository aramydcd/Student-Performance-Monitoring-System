import streamlit as st, pandas as pd
from utils.rbac import allow_roles
from utils.models import list_students_in_course, upsert_score, get_scores,add_notification,get_user_id_by_email
from utils.db import get_conn

@allow_roles("lecturer","student")
def main():
    st.set_page_config(page_title="EduShield | 📝 Assessments", page_icon="images/Edushield_Icon1.png", layout="wide")

    st.title("📝 Assessments")
    u = st.session_state["user"]

    # Session/Semester Selection
    st.markdown("--------------------")
    st.subheader("🔍 Session/Semester Filter")
    col1, col2 = st.columns(2)
    with col1:
        session = st.selectbox("📅 Session", ["2024/2025"])
    with col2:
        semester = st.selectbox("🏫 Semester", ["First", "Second"])

    if u["role"]=="lecturer":
        with get_conn() as conn:
            mine = conn.execute("""SELECT lc.id, c.id AS course_id, c.code, c.title
                                   FROM lecturer_courses lc JOIN courses c ON c.id=lc.course_id
                                   WHERE lc.lecturer_id=? AND lc.session=? AND lc.semester=?
                                   ORDER BY c.code""",(u["id"],session,semester)).fetchall()
        if not mine:
            st.info("Add courses in Lecturer Portal first.")
            return
        
        label = col1.selectbox("Course", [f"{m['code']} - {m['title']}" for m in mine])
        chosen = [m for m in mine if f"{m['code']} - {m['title']}"==label][0]
        component = col2.selectbox("Component", ["Test","Assignment","Exam"])
        students = list_students_in_course(chosen["course_id"], session, semester)
        st.divider()
        
        st.subheader("Enter Scores")
        if students:
            with st.expander(f"Record Scores for {chosen["code"]} {component}"):
                for s in students:
                    user_id = get_user_id_by_email(s["email"])
                    score = st.number_input(f"{s['full_name']}", 0.0, 100.0, 0.0, step=1.0, key=f"sc_{user_id}")
                    if st.button(f"Save Score", key=f"save_sc_{user_id}"):
                        upsert_score(chosen["course_id"], user_id, component.lower(), score, u["id"])
                        add_notification(
                            title=f"New scores posted for {chosen['code']}",
                            message=f"Scores for {component} were posted. Check your dashboard.",
                            course_id=chosen["course_id"]
                        )

                        st.success("Saved.")
        st.divider()
    else:
        # students will view scores in dashboard

        st.markdown("--------------------")

        scores = get_scores(u["id"])
        st.subheader("Assessments & Assignment Scores")
        if scores:
            st.dataframe(pd.DataFrame(scores))
        else:
            st.info("No Assessments/Assignment score recorded yet!.")

        st.markdown("---------------")


if __name__ == "__main__":
    main()
