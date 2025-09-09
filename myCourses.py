import streamlit as st
import pandas as pd
import os
from utils.rbac import allow_roles
from utils.models import (
    student_enrollments,
    list_resources_for_course,
    list_lecturer_courses,
    allocate_course_to_lecturer,
    add_course,
    save_resource,
    delete_resource,
    add_notification,
    count_users_by_role,
    count_courses,
    count_resources,
    list_all_courses,
    delete_course,
    get_all_lecturers,
    list_course_lecturers,
    list_course_students,
    get_user_id_by_email,
    lecturer_pick_course
)
from utils.db import get_conn

@allow_roles("student", "lecturer", "admin")
def main():
    st.set_page_config(page_title="EduShield | 📚 Course Management", page_icon="images/Edushield_Icon1.png", layout="wide")

    u = st.session_state["user"]
    role = u["role"]

    if role in ["student", "lecturer"]:
        st.title("📚 My Courses & Resources Management")
        st.caption("Manage your courses and  materials")
    else:
        st.title("📚 Course Management")
        st.caption("Manage courses, materials, and student enrollments")
    st.markdown("---------------------")

    # Session/Semester Selection
    st.subheader("🔍 Session/Semester Filter")
    col1, col2 = st.columns(2)
    with col1:
        session = st.selectbox("📅 Session", ["2024/2025"])
    with col2:
        semester = st.selectbox("🏫 Semester", ["First", "Second"])
    st.markdown("---------------------")

    if role == "student":
        st.subheader("🎒 My Courses")
        level = u["level"] or "ND1"
        st.caption(f"Level: {level}")
        
        # Enrolled courses
        enrolls = student_enrollments(u["id"], session, semester)
        if enrolls:
            df = pd.DataFrame(enrolls)[["Course Code", "Course Title", "Course Units", "Session", "Semester"]]
            st.dataframe(df)
        else:
            st.info("You are not enrolled in any courses this semester.")

        st.markdown("---------------------")
        
        
        # Access resources for enrolled courses
        st.subheader("📂 Course Materials")
        # st.markdown("---------------------")
        resource_availability_status = []
        course_codes = [c["Course Code"] for c in enrolls]
        print(len(course_codes))
        for code in course_codes:
            title = [c["Course Title"] for c in enrolls if c["Course Code"] == code]
            unit =  [c["Course Units"] for c in enrolls if c["Course Code"] == code]
            resources = list_resources_for_course(code)
            if resources:
                resource_availability_status.append(True)
                with st.expander(f"{code} - {title[0]} ({unit[0]} units)"):
                    for r in resources:
                        st.write(f"👨‍🏫 **Lecturer:** {r['lecturer_name'].title()}")
                        with st.expander(f"**Material Title:** {r['title'].title()} (🗓️{r['created_at']})"):
                            st.write(f"Description: {r["description"].title() or "No Description"}")
                            st.download_button(
                                label="⬇️ Download Material",
                                data=open(r["file_path"], "rb").read(),
                                file_name=os.path.basename(r["file_path"]),
                            )
            else:
                if len(course_codes) > 1:
                    st.info(f"No resources uploaded for {code} yet.")

        if len(resource_availability_status) == 0:
            st.info(f"No resources uploaded yet.")
        
        st.markdown("---------------------")

    elif role == "lecturer":
        st.subheader("🎒 My Courses")
        courses = list_lecturer_courses(u["id"], session, semester)
        if courses:
            df = pd.DataFrame(courses)[["code", "title", "units"]]
            st.dataframe(df)
        else:
            st.info("No courses allocated. Ask admin to allocate courses.")

        # Upload resources
        st.markdown("---------------------")
        st.subheader("📤 **Upload Course Materials**")
        with st.expander("Start Uploading ⬆️"):
            selected_course = st.selectbox("Select Course", [f"{c['code']} - {c['title']}" for c in courses]) if courses else None
            if selected_course:
                course_id = [c["id"] for c in courses if f"{c['code']} - {c['title']}" == selected_course][0]
                title = st.text_input("Resource Title")
                description = st.text_area("Description")
                uploaded_file = st.file_uploader(f"Upload course material", type=["pdf","docx","pptx","txt"])
                
                if st.button("📤 Upload Resource"):
                    if uploaded_file is not None:
                        save_resource(course_id, u["id"], title, description, uploaded_file)
                        add_notification(
                            title=f"New Material Uploaded for {selected_course}",
                            # message=f"Lecture notes for {selected_course} have been uploaded.",
                            message=f"{u['full_name']} uploaded '{title}' for {selected_course}.",
                            course_id=course_id
                        )

                        st.success("✅ Resource uploaded successfully")
                    else:
                        st.warning("Please, upload a file!")
        st.markdown("---------------------")

        # -----------------------------------
        # List & Manage Existing Resources
        # -----------------------------------
        st.subheader("📂 **Existing Resources**")
      
        if not courses:
            st.info("No registered courses found.")
        else:
            for c in courses:
                with st.expander(f"{c['code']} - {c['title']}"):
                    # Fetch resources for this course
                    resources = list_resources_for_course(c["code"])
                    my_resources = [r for r in resources if r["lecturer_name"] == u["full_name"]]

                    if not my_resources:
                        st.info("No resources uploaded yet.")
                    else:
                        for r in my_resources:
                            with st.expander(f"📄 {r['title']} ({os.path.basename(r['file_path'])})"):
                                st.write(f"**Description:** {r['description']}")
                                st.write(f"📅 Uploaded: {r['created_at']}")

                                col1,col2 = st.columns(2)
                                # Download button
                                col1.download_button(
                                    label="⬇️ Download",
                                    data=open(r["file_path"], "rb").read(),
                                    file_name=os.path.basename(r["file_path"]),
                                    key=f"dl_{r['id']}"
                                )

                                # Delete button
                                if col2.button("🗑️ Delete", key=f"del_{r['id']}"):
                                    delete_resource(r["id"])
                                    st.warning("Resource deleted!")
                                    st.rerun()
        st.divider()

    elif role == "admin":
        st.markdown("### 📊 Quick Stats")
        # lecturer_courses = list_lecturer_courses(st.session_state.user["id"],session,semester)
        
        total_students = count_users_by_role('student')
        total_materials = count_resources()

        col1, col2, col3 = st.columns(3)
        col1.metric("Courses", count_courses())
        col2.metric("Enrolled Students", total_students)
        col3.metric("Resources", total_materials)

        st.markdown("---")
        admin_course_management(session,semester)


def admin_course_management(session,semester):
    # st.title("📚 Course Management (Admin)")

    tab1, tab2, tab3 = st.tabs(["📖 Courses", "➕ Add Course", "👨‍🏫 Allocate Courses"])

    # ------------------ TAB 1: LIST COURSES ------------------
    with tab1:
        st.subheader("All Courses")
        courses = list_all_courses()
        if not courses:
            st.info("No courses available yet.")
        else:
            for course in courses:
                with st.expander(f"{course['code']} - {course['title']} ({course['level']})"):
                    st.write(f"**Units:** {course['units']}")
                    st.write(f"**Semester:** {semester} | **Session:** {session}")

                    # Show lecturers
                    lecturers = list_course_lecturers(course["id"])
                    if lecturers:
                        st.write("👨‍🏫 **Lecturers:** " + ", ".join([l["full_name"] for l in lecturers]))
                    else:
                        st.warning("⚠️ No lecturer allocated.")

                    # Show students
                    students = list_course_students(course["id"], session, semester)
                    st.write(f"👨‍🎓 **Enrolled Students:** {len(students)}")
                    if students:
                        df = pd.DataFrame(students)
                        st.dataframe(df, use_container_width=True)
                        # st.dataframe(pd.DataFrame(students), use_container_width=True)

                    st.write("📂 **Course Materials:**")
                    
                    with st.expander(f"{course['code']} - {course['title']}"):
                        # Fetch resources for this course
                        resources = list_resources_for_course(course["code"])
                        all_resources = [r for r in resources]

                        if not all_resources:
                            st.info("No resources uploaded yet.")
                        else:
                            for r in all_resources:
                                with st.expander(f"📄 {r['title']} ({os.path.basename(r['file_path'])})"):
                                    st.write(f"**Description:** {r['description']}")
                                    st.write(f"📅 Uploaded: {r['created_at']}")

                                    col1,col2 = st.columns(2)
                                    # Download button
                                    col1.download_button(
                                        label="⬇️ Download",
                                        data=open(r["file_path"], "rb").read(),
                                        file_name=os.path.basename(r["file_path"]),
                                        key=f"dl_{r['id']}"
                                    )

                                    # Delete button
                                    if col2.button("🗑️ Delete", key=f"del_{r['id']}"):
                                        delete_resource(r["id"])
                                        st.warning("Resource deleted!")
                                        st.rerun()
                    # st.divider()
                    

                    # Delete option
                    if st.button(f"❌ Delete {course['code']}", key=f"delete_{course['id']}"):
                        delete_course(course["id"])
                        st.success(f"Course {course['code']} deleted successfully!")
                        st.rerun()

    # ------------------ TAB 2: ADD COURSE ------------------
    with tab2:
        st.subheader("➕ Add a New Course")

        code = st.text_input("Course Code (e.g. COM101)")
        title = st.text_input("Course Title")
        units = st.number_input("Units", min_value=1, max_value=6, step=1)
        level = st.selectbox("Level", ["ND1", "ND2", "HND1", "HND2"])
        semester = st.selectbox("Semester", ["First", "Second"])
        session = st.text_input("Session (e.g. 2024/2025)")

        if st.button("✅ Add Course"):
            if not code or not title or not session:
                st.error("⚠️ Please fill all fields.")
            else:
                add_course(code, title, units, level, semester, session)
                st.success(f"Course {code} - {title} added successfully!")
                st.rerun()

    # ------------------ TAB 3: ALLOCATE COURSE ------------------
    with tab3:
        st.subheader("👨‍🏫 Allocate Courses to Lecturers")

        courses = list_all_courses()
        lecturers = get_all_lecturers()

        if not courses:
            st.warning("⚠️ No courses available to allocate.")
        elif not lecturers:
            st.warning("⚠️ No lecturers found.")
        else:
            course_options = {f"{c['code']} - {c['title']}": c for c in courses}
            lecturer_options = {l['Fullname']: l for l in lecturers}

            course_choice = st.selectbox("Select Course", list(course_options.keys()))
            lecturer_choice = st.selectbox("Select Lecturer", list(lecturer_options.keys()))
            # session = st.text_input("Session (e.g. 2024/2025)")
            # semester = st.selectbox("Semester", ["First", "Second"])

            if st.button("📌 Allocate"):
                course = course_options[course_choice]
                lecturer = lecturer_options[lecturer_choice]
                lecturer_id = get_user_id_by_email(lecturer['Email'])
                # st.markdown(lecturer)
                lecturer_pick_course(lecturer_id, course["id"], session, semester)
                st.success(f"✅ {lecturer['Fullname']} allocated to {course['code']} ({session} - {semester})")
    st.divider()


if __name__ == "__main__":
    main()
