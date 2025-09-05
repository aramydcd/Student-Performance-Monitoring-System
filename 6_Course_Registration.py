import streamlit as st, pandas as pd
from utils.rbac import allow_roles
from utils.models import (
    list_courses_for_level, enroll_student, student_enrollments, drop_student_course,lecturer_pick_course,drop_lecturer_course,
    get_course_ids,list_all_courses
)

@allow_roles("student","admin","lecturer")
def main():
    
    u = st.session_state["user"]

    if u['role'] == "lecturer":
        st.set_page_config(page_title="EduShield | 📖 Course Management", page_icon="images/Edushield_Icon1.png", layout="wide")

        st.title("📖 Course Management")
    else:
        st.set_page_config(page_title="EduShield | 🧾 Course Registration", page_icon="images/Edushield_Icon1.png", layout="wide")

        st.title("🧾 Course Registration")


    # Session/Semester Selection
    st.markdown("--------------------")
    st.subheader("🔍 Session/Semester Filter")
    col1, col2 = st.columns(2)
    with col1:
        session = st.selectbox("📅 Session", ["2024/2025"])
    with col2:
        semester = st.selectbox("🏫 Semester", ["First", "Second"])

    if u["role"]=="student":
        level = u["level"] or "ND1"

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
        st.caption(f"Level: {level}")
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
    
        st.subheader("📋 My Registered Courses")
        if registered:
            df = pd.DataFrame(registered)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("You are not enrolled in any courses this semester.")

        st.markdown("---------------")
        st.subheader("🗑️ Drop Courses")
        if registered:
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
            st.info("You are not enrolled in any courses this semester.")
    
    elif u["role"]=="lecturer":
        lecturer_course_page(u, session, semester)
    
    else:
        st.write("Admins can register students by impersonation (future enhancement).")
    
    st.markdown("---------------")



def lecturer_course_page(u: dict, session , semester):
    """
    Lecturer course management:
    - Register for courses
    - See registered courses
    - Drop courses
    """
     # -------------------------------
    # Fetch lecturer's current courses
    # -------------------------------
    st.divider()
    st.subheader("✍️ Register Course")
    mine = get_course_ids(u["id"], session, semester)

    my_course_ids = [m["code"] for m in mine]  # already registered

    # -------------------------------
    # Add Courses to Teach
    # -------------------------------
    courses = list_all_courses()

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

    st.divider()
    # -------------------------------
    # Course Summary
    # -------------------------------
    st.subheader("📋 My Registered Courses")
    # st.subheader("📊 My Courses Summary")

    if mine:
        df_courses = pd.DataFrame(mine)
        df_courses = df_courses.rename(columns={
            "id": "Record ID",
            "code": "Course Code",
            "title": "Course Title"
        })
        st.metric("Total Courses", len(df_courses))
        st.dataframe(df_courses, use_container_width=True)
    else:
        st.info("You have not registered for any courses this semester.")

    st.divider()

    # -------------------------------
    # Drop Courses
    # -------------------------------
    st.subheader("🗑️ Drop Courses")

    if mine:  # lecturer's registered courses
        allow_drop = True   # later configurable by admin rules
        if allow_drop:
            drop_pick = st.selectbox(
                "Select course to drop", 
                [f"{m['code']} - {m['title']}" for m in mine]
            )

            if st.button("❌ Drop selected"):
                course_code = drop_pick.split(" - ")[0]  # extract course code
                deleted = drop_lecturer_course(u["id"], course_code, session, semester)
                if deleted:
                    st.warning(f"Dropped {drop_pick}")
                    st.rerun()
                else:
                    st.error("Could not drop course (maybe not found).")
        else:
            st.info("Dropping courses is not allowed this semester.")
    else:
        st.info("You are not registered for any courses this semester.")


    

if __name__ == "__main__":
    main()


# """
# course management ----  lecturer
# course allocation ----- admin
# """