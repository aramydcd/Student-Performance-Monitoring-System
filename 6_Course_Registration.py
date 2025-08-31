import streamlit as st, pandas as pd
from utils.rbac import allow_roles
from utils.models import list_courses_for_level, enroll_student, student_enrollments, drop_student_course

@allow_roles("student","admin")
def main():
    st.title("🧾 Course Registration")
    u = st.session_state["user"]

    col1,col2 = st.columns(2)
    session = col1.selectbox("Session", ["2024/2025"])
    semester = col2.selectbox("Semester", ["First","Second"])

    if u["role"]=="student":
        level = u["level"] or "ND1"
        st.caption(f"Level: {level}")

        # Get already registered courses
        registered = student_enrollments(u["id"], session, semester)
        registered_ids = {c["Course Code"] for c in registered}

        # List all courses for the level
        courses = list_courses_for_level(level)

        # Filter to only unregistered ones
        available_courses = [c for c in courses if c["code"] not in registered_ids]

        # --- Register new courses ---
        st.markdown("---------------")
        st.subheader("✍️ Register New Course")
        if available_courses:
            picks = st.multiselect("Select courses", [f"{c['code']} - {c['title']} ({c['units']}u)" for c in available_courses])
            submit = st.button("✅ Register Selected")
            if submit:
                if picks:
                    ids = [c["id"] for c in available_courses if f"{c['code']} - {c['title']} ({c['units']}u)" in picks]
                    for cid in ids:
                        enroll_student(u["id"], cid, session, semester)
                    st.success("Registration saved.")
                    st.rerun()
                else:
                    st.warning("Please, select course you want to register!")
        else:
            st.info("All courses for your level are already registered.")

        
        st.markdown("---------------")
        # allow dropping
        if registered:
            st.subheader("📋 My Registered Courses")
            df = pd.DataFrame(registered)
            st.dataframe(df, use_container_width=True)

            st.markdown("---------------")
            st.subheader("🗑️ Drop Courses")
            allow_drop = True   # later make this configurable by admin rules
            if allow_drop:

                drop_pick = st.selectbox("Select courses to drop", [r["Course Code"] for r in registered])

                if st.button("❌ Drop selected"):
                    deleted = drop_student_course(u["id"], drop_pick, session, semester)
                    if deleted:
                        st.warning(f"Dropped {drop_pick}")
                        st.rerun()
                    else:
                        st.error("Could not drop course (maybe not found).")
            else:
                st.info("Dropping courses is not allowed this semester.")
    else:
        st.write("Admins can register students by impersonation (future enhancement).")

if __name__ == "__main__":
    main()


# """
# course management ----  lecturer
# course allocation ----- admin
# """