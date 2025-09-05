import streamlit as st
import pandas as pd
from utils.rbac import allow_roles
from utils.db import get_conn
import os


def student_courses(student_id: int, session: str, semester: str):
    """Fetch student enrolled courses with lecturer + resources."""
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT c.id AS course_id, c.code, c.title, c.units,
                   l.full_name AS lecturer_name, l.email AS lecturer_email,
                   r.id AS resource_id, r.file_path, r.description
            FROM enrollments e
            JOIN courses c ON c.id = e.course_id
            LEFT JOIN lecturers l ON c.lecturer_id = l.id
            LEFT JOIN resources r ON r.course_id = c.id
            WHERE e.student_id=? AND e.session=? AND e.semester=?
            ORDER BY c.code
        """, (student_id, session, semester))
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]


def lecturer_courses(lecturer_id: int):
    """Fetch courses taught by lecturer."""
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT c.id AS course_id, c.code, c.title, c.units
            FROM courses c
            WHERE c.lecturer_id=?
            ORDER BY c.code
        """, (lecturer_id,))
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]


def get_resources(course_id: int):
    """Fetch all resources for a course."""
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT id, description, file_path, created_at
            FROM resources
            WHERE course_id=?
            ORDER BY created_at DESC
        """, (course_id,))
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]


def save_resource(course_id: int, description: str, file):
    """Save uploaded file and insert into DB."""
    os.makedirs("uploads", exist_ok=True)
    filepath = os.path.join("uploads", file.name)
    with open(filepath, "wb") as f:
        f.write(file.getbuffer())

    with get_conn() as conn:
        conn.execute("""
            INSERT INTO resources(course_id, description, file_path)
            VALUES (?, ?, ?)
        """, (course_id, description, filepath))
        conn.commit()


def delete_resource(resource_id: int):
    """Delete resource from DB and file system."""
    with get_conn() as conn:
        cur = conn.execute("SELECT file_path FROM resources WHERE id=?", (resource_id,))
        row = cur.fetchone()
        if row and os.path.exists(row[0]):
            os.remove(row[0])  # remove file
        conn.execute("DELETE FROM resources WHERE id=?", (resource_id,))
        conn.commit()


@allow_roles("student", "lecturer")
def main():
    st.title("📖 My Courses")
    u = st.session_state["user"]

    if u["role"] == "student":
        session = st.selectbox("Session", ["2024/2025"])
        semester = st.selectbox("Semester", ["First", "Second"])

        courses = student_courses(u["id"], session, semester)
        if not courses:
            st.info("You are not enrolled in any courses yet.")
            return

        for c in courses:
            with st.expander(f"{c['code']} - {c['title']} ({c['units']} units)"):
                st.write(f"👨‍🏫 **Lecturer:** {c.get('lecturer_name','N/A')} ({c.get('lecturer_email','-')})")

                if c["file_path"]:
                    st.subheader("📂 Course Materials")
                    st.write(c["description"] or "No description")
                    st.download_button(
                        label="⬇️ Download Material",
                        data=open(c["file_path"], "rb").read(),
                        file_name=os.path.basename(c["file_path"]),
                    )
                else:
                    st.info("No resources uploaded yet for this course.")

    elif u["role"] == "lecturer":
        st.subheader("👨‍🏫 My Teaching Courses")
        courses = lecturer_courses(u["id"])

        if not courses:
            st.warning("You are not assigned to any courses yet.")
            return

        for c in courses:
            with st.expander(f"{c['code']} - {c['title']} ({c['units']} units)"):
                # Upload Section
                st.write("📂 **Upload Course Materials**")
                desc = st.text_input(f"Description for {c['code']}", key=f"desc_{c['id']}")
                file = st.file_uploader(f"Upload file for {c['code']}", type=["pdf", "pptx", "docx"], key=f"file_{c['id']}")
                if file and st.button(f"Upload for {c['code']}", key=f"btn_{c['id']}"):
                    save_resource(c["course_id"], desc, file)
                    st.success("Resource uploaded successfully!")

                # List & Manage Resources
                st.write("📑 **Existing Resources**")
                resources = get_resources(c["course_id"])
                if not resources:
                    st.info("No resources uploaded yet.")
                else:
                    for r in resources:
                        col1, col2, col3 = st.columns([3, 2, 1])
                        with col1:
                            st.write(f"📄 {r['description']} ({os.path.basename(r['file_path'])})")
                        with col2:
                            st.download_button(
                                label="⬇️ Download",
                                data=open(r["file_path"], "rb").read(),
                                file_name=os.path.basename(r["file_path"]),
                                key=f"dl_{r['id']}"
                            )
                        with col3:
                            if st.button("🗑️ Delete", key=f"del_{r['id']}"):
                                delete_resource(r["id"])
                                st.warning("Resource deleted!")
                                st.rerun()


if __name__ == "__main__":
    main()
