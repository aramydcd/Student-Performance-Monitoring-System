import streamlit as st
import pandas as pd
from utils.rbac import allow_roles
from utils.models import (
    student_enrollments,
    list_courses_for_level,
    enroll_student,
    list_resources_for_course,
    list_lecturer_courses,
    allocate_course_to_lecturer,
    add_course
)
from utils.db import get_conn

@allow_roles("student", "lecturer", "admin")
def main():
    st.title("📚 Courses Module")
    u = st.session_state["user"]
    role = u["role"]

    session = st.selectbox("Session", ["2024/2025"])
    semester = st.selectbox("Semester", ["First", "Second"])

    if role == "student":
        st.subheader("My Courses")
        level = u["level"] or "ND1"
        st.caption(f"Level: {level}")
        
        # Enrolled courses
        enrolls = student_enrollments(u["id"], session, semester)
        if enrolls:
            df = pd.DataFrame(enrolls)[["Course Code", "Course Title", "Course Units", "Session", "Semester"]]
            st.dataframe(df)
        else:
            st.info("You are not enrolled in any courses this semester.")
        
        # Access resources for enrolled courses
        course_codes = [c["Course Code"] for c in enrolls]
        for code in course_codes:
            st.markdown(f"### Resources for {code}")
            resources = list_resources_for_course(code)
            if resources:
                for r in resources:
                    with st.expander(f"{r['title'].title()} by {r['lecturer_name'].title()}"):
                        st.write(r["description"].title())
                        st.write(f"Uploaded: {r['created_at']}")
                        st.markdown(f"[Download]({r['file_path']})")
            else:
                st.info("No resources uploaded yet.")

    elif role == "lecturer":
        st.subheader("My Courses")
        courses = list_lecturer_courses(u["id"], session, semester)
        if courses:
            df = pd.DataFrame(courses)[["code", "title", "units"]]
            st.dataframe(df)
        else:
            st.info("No courses allocated. Ask admin to allocate courses.")

        # Upload resources
        st.markdown("### Upload Course Resource")
        selected_course = st.selectbox("Select Course", [f"{c['code']} - {c['title']}" for c in courses]) if courses else None
        if selected_course:
            course_id = [c["id"] for c in courses if f"{c['code']} - {c['title']}" == selected_course][0]
            title = st.text_input("Resource Title")
            description = st.text_area("Description")
            uploaded_file = st.file_uploader("Upload course material", type=["pdf","docx","pptx","txt"])
            
            if st.button("Upload Resource"):
                if uploaded_file is not None:
                    # Save file to a folder (e.g., resources/)
                    file_path = f"resources/{uploaded_file.name}"
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                     # Insert into database

                    with get_conn() as conn:
                        conn.execute("""
                            INSERT INTO resources (course_id, lecturer_id, title, description, file_path)
                            VALUES (?, ?, ?, ?, ?)
                        """, (course_id, u["id"], title, description, file_path))
                        conn.commit()
                        st.success("✅ Resource uploaded successfully")

                else:
                    st.warning("Please, upload a file!")

    elif role == "admin":
        st.subheader("Course Management")
        # Add new course
        st.markdown("### Add New Course")
        code = st.text_input("Course Code")
        title = st.text_input("Course Title")
        units = st.number_input("Units", min_value=1, max_value=10, step=1)
        level = st.selectbox("Level", ["ND1", "ND2", "HND1", "HND2"])
        if st.button("Add Course"):
            add_course(code, title, units, level)
            st.success("Course added successfully!")

        # Allocate course to lecturer
        st.markdown("### Allocate Course to Lecturer")
        with get_conn() as conn:
            lecturers = conn.execute("SELECT id, full_name FROM users WHERE role='lecturer'").fetchall()
            courses = conn.execute("SELECT id, code, title FROM courses").fetchall()
        
        lecturer_choice = st.selectbox("Select Lecturer", [f"{l['full_name']}" for l in lecturers]) if lecturers else None
        course_choice = st.selectbox("Select Course", [f"{c['code']} - {c['title']}" for c in courses]) if courses else None
        if st.button("Allocate Course"):
            if lecturer_choice and course_choice:
                lecturer_id = [l["id"] for l in lecturers if l["full_name"] == lecturer_choice][0]
                course_id = [c["id"] for c in courses if f"{c['code']} - {c['title']}" == course_choice][0]
                allocate_course_to_lecturer(lecturer_id, course_id, session, semester)
                st.success("Course allocated to lecturer successfully!")

if __name__ == "__main__":
    main()
