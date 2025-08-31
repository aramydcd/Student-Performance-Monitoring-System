import streamlit as st, pandas as pd, datetime
from utils.rbac import allow_roles
from utils.models import list_students_in_course, mark_attendance, get_attendance, attendance_summary
from utils.db import get_conn

@allow_roles("lecturer","student")
def main():
    st.title("🗓️ Attendance")
    st.caption("Manage and track attendance records.")

    u = st.session_state["user"]

    # Session/Semester filter
    col1, col2 = st.columns(2)
    session = col1.selectbox("Session", ["2024/2025"])
    semester = col2.selectbox("Semester", ["First","Second"])
    st.markdown("-----------------")

    if u["role"]=="lecturer":
        # ✅ Lecturer view: mark attendance
        with get_conn() as conn:
            mine = conn.execute("""SELECT lc.id, c.id AS course_id, c.code, c.title
                                   FROM lecturer_courses lc JOIN courses c ON c.id=lc.course_id
                                   WHERE lc.lecturer_id=? AND lc.session=? AND lc.semester=?
                                   ORDER BY c.code""",(u["id"],session,semester)).fetchall()
        if not mine:
            st.info("⚠️ You have no assigned courses this semester. Please add them in Lecturer Portal.")
            st.info("Add courses in Lecturer Portal first.")
            return
        
        # Course selector
        label = st.selectbox("Course", [f"{m['code']} - {m['title']}" for m in mine])
        chosen = [m for m in mine if f"{m['code']} - {m['title']}"==label][0]

        class_date = st.date_input("Class Date", datetime.date.today()).isoformat()

        # Load students in that course
        students = list_students_in_course(chosen["course_id"], session, semester)

        st.write("Mark presence:")
        for s in students:
            present = st.checkbox(s["full_name"], value=True, key=f"att_{s['id']}")
            if st.button(f"Save {s['full_name']}", key=f"save_{s['id']}"):
                mark_attendance(chosen["course_id"], s["id"], class_date, present, u["id"])
                st.success("✅ Saved.")
    else:
        # ✅ Student view: read-only attendance summary

        # Attendance % by course
        st.subheader("📊 Attendance Summary (% by Course)")
        summary = attendance_summary(u["id"])
        if summary:
            df_summary = pd.DataFrame(summary)

            # Add emoji based on risk level
            def add_status(pct):
                if pct >= 75:
                    return f"✅ {pct:.1f}%"
                elif pct >= 50:
                    return f"⚠️ {pct:.1f}%"
                else:
                    return f"❌ {pct:.1f}%"

            df_summary["Attendance %"] = df_summary["Attendance %"].apply(add_status)
            st.dataframe(df_summary, use_container_width=True)

            # Quick Stat: Average Attendance %
            avg_attendance = sum(v["Attendance %"] for v in summary) / len(summary)

            # Color-coding thresholds
            if avg_attendance >= 75:
                st.metric("📌 Average Attendance", f"{avg_attendance:.1f}%", delta="✅ Good")
            elif avg_attendance >= 50:
                st.metric("📌 Average Attendance", f"{avg_attendance:.1f}%", delta="⚠️ Fair")
            else:
                st.metric("📌 Average Attendance", f"{avg_attendance:.1f}%", delta="❌ At Risk")
        else:
            st.info("No Attendance records found for this session/semester.")

        st.markdown("-----------------")        

        # Detailed attendance
        st.subheader("📋 Detailed Attendance Records")
        details = get_attendance(u["id"])
        if details:
            st.dataframe(pd.DataFrame(details))
        else:
            st.info("No detailed attendance records found for this session/semester.")



if __name__ == "__main__":
    main()
