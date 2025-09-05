import streamlit as st, pandas as pd, datetime
from utils.rbac import allow_roles
from utils.models import list_students_in_course, mark_attendance, get_attendance, attendance_summary, add_notification,get_user_id_by_email
from utils.db import get_conn

@allow_roles("lecturer","student")
def main():
    st.set_page_config(page_title="EduShield | 🗓️ Attendance", page_icon="images/Edushield_Icon1.png", layout="wide")

    st.title("🗓️ Attendance")
    st.caption("Manage and track attendance records.")

    u = st.session_state["user"]

    # Session/Semester Selection
    st.markdown("--------------------")
    st.subheader("🔍 Session/Semester Filter")
    col1, col2 = st.columns(2)
    with col1:
        session = st.selectbox("📅 Session", ["2024/2025"])
    with col2:
        semester = st.selectbox("🏫 Semester", ["First", "Second"])
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
        
        st.subheader("🗓️ Take Attendance")
        with st.expander(f"Mark Attendance for 📆 {datetime.date.today()}"):
            # Course selector
            col1,col2  = st.columns(2)
            label = col1.selectbox("Course", [f"{m['code']} - {m['title']}" for m in mine])
            chosen = [m for m in mine if f"{m['code']} - {m['title']}"==label][0]

            class_date = col2.date_input("Class Date", datetime.date.today()).isoformat()
            st.divider()

            # Load students in that course
            students = list_students_in_course(chosen["course_id"], session, semester)
            # st.dataframe(pd.DataFrame(students), use_container_width=True)

            st.subheader(f"Students who enrolled for {chosen['code']}")
            if students:
                st.write("Mark presence:")
                for s in students:
                    user_id = get_user_id_by_email(s["email"])
                    present = st.checkbox(s["full_name"], value=True, key=f"att_{user_id}")
                    if st.button(f"Save Attendance", key=f"save_{user_id}"):
                        mark_attendance(chosen["course_id"], user_id, class_date, present, u["id"])
                        add_notification(
                            title=f"Attendance marked for {chosen["code"]}",
                            message=f"Attendance for {class_date} has been recorded.",
                            course_id=chosen["course_id"]
                        )

                        st.success("✅ Saved.")
            else:
                st.info(f"No student have enrolled for {chosen['code']}")
        st.divider()

        # 📊 Attendance Summary (% by Students)
        st.subheader("📊 Attendance Summary")

        with st.expander("Attendance Summary (% by Course)"):
            course_reg = [f"{m['code']} - {m['title']}" for m in mine]
            selection = st.selectbox("📘 Select Course", course_reg, key="course_summary")

            chosen = [m for m in mine if f"{m['code']} - {m['title']}" == selection][0]

            # ✅ Load enrolled students
            students = list_students_in_course(chosen["course_id"], session, semester)

            if not students:
                st.warning("⚠️ No students enrolled in this course.")
            else:
                # 🔹 Attendance % per student
                summary_rows = []
                for s in students:
                    user_id = get_user_id_by_email(s["email"])
                    summ = attendance_summary(user_id)
                    # filter to this course only
                    for rec in summ:
                        if rec["Course Code"] == chosen["code"]:
                            summary_rows.append({
                                "Student": s["full_name"],
                                "Attendance %": rec["Attendance %"]
                            })
                st.divider()
                if summary_rows:
                    df_summary = pd.DataFrame(summary_rows)
                    st.markdown("### 📌 Attendance Percentage by Student")
                    st.dataframe(df_summary, use_container_width=True)

                    # Download option
                    st.download_button(
                        "⬇️ Download Attendance Summary (CSV)",
                        data=df_summary.to_csv(index=False),
                        file_name=f"attendance_summary_{chosen['code']}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No attendance records yet for this course.")

                # 🔹 Detailed attendance by date
                st.divider()
                st.markdown("### 📅 Detailed Attendance Records")
                all_records = []
                for s in students:
                    user_id = get_user_id_by_email(s["email"])
                    recs = get_attendance(user_id)
                    for r in recs:
                        if r["Course Code"] == chosen["code"]:
                            r["Student"] = s["full_name"]
                            all_records.append(r)

                if all_records:
                    df_detail = pd.DataFrame(all_records)

                    # Get available dates for filtering
                    unique_dates = sorted(df_detail["Class Date"].unique())
                    chosen_date = st.selectbox("Select Class Date", unique_dates, key="date_summary")

                    filtered = df_detail[df_detail["Class Date"] == chosen_date][
                        ["Student", "Course Code", "Class Date", "Status", "Marked By"]
                    ]
                    st.dataframe(filtered, use_container_width=True)
                else:
                    st.info("No detailed attendance records available yet.")

            


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

        st.markdown("---------------")


if __name__ == "__main__":
    main()
