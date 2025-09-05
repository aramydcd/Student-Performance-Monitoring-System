import streamlit as st
import pandas as pd
import bcrypt,sqlite3
import matplotlib.pyplot as plt
from utils.rbac import allow_roles
from utils.models import (
    all_users, create_user, get_user_by_email,
    count_users_by_role, count_courses,
    get_avg_gpa, get_avg_attendance, get_system_alerts
)



@allow_roles("admin")
def main():
    st.set_page_config(page_title="EduShield | 🛡️ Dashboard", page_icon="images/Edushield_Icon1.png", layout="wide")

    st.title("🛡️ Admin Panel")

    u = st.session_state["user"]
    st.success(f"👋 Welcome, {u['full_name']}!")

    st.caption("🛡️ “Secure. Manage. Lead — keeping EduShield running strong.”")
    st.divider()
    # =============================
    # 1. SYSTEM OVERVIEW
    # =============================
    st.subheader("📊 System Overview")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👨‍🎓 Students", count_users_by_role("student"))
    with col2:
        st.metric("👨‍🏫 Lecturers", count_users_by_role("lecturer"))
    with col3:
        st.metric("📚 Courses", count_courses())
    st.divider()

    # =============================
    # 2. QUICK STATS
    # =============================
    st.subheader("⚡ Quick Stats")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📈 Avg GPA", f"{get_avg_gpa():.2f}")
    with col2:
        st.metric("🕒 Avg Attendance", f"{get_avg_attendance():.1f}%")
    with col3:
        alerts = get_system_alerts()
        st.metric("🚨 System Alerts", len(alerts))

    if alerts:
        with st.expander("🔔 View Alerts"):
            for a in alerts:
                st.warning(f"⚠️ {a}")
    st.divider()

    # =============================
    # 3. VISUAL INSIGHTS
    # =============================
    st.subheader("📉 System Insights")

    users = all_users()
    if users:
        df_users = pd.DataFrame(users)

        # st.subheader("Role Distribution")

        with st.expander("View Insights"):
            col1, col2 = st.columns(2)

        # --- Role Distribution ---
        with col1:
            with st.expander("User Role Distribution"):
                role_counts = df_users["Role"].value_counts()
                fig, ax = plt.subplots()
                role_counts.plot(kind="bar", ax=ax)
                ax.set_title("User Role Distribution")
                ax.set_ylabel("Count")
                st.pyplot(fig)

        # --- GPA Distribution (students only) ---
        with col2:
            with st.expander("GPA Distribution"):
                if "gpa" in df_users.columns:
                    student_gpa = df_users[df_users["role"]=="student"]["gpa"].dropna()
                    if not student_gpa.empty:
                        fig, ax = plt.subplots()
                        student_gpa.plot(kind="hist", bins=10, ax=ax)
                        ax.set_title("GPA Distribution")
                        ax.set_xlabel("GPA")
                        st.pyplot(fig)
                    else:
                        st.info("No GPA records yet.")
                else:
                    st.info("No GPA field available in users table.")
    st.divider()

    # =============================
    # 4. USER MANAGEMENT
    # =============================
    st.subheader("👥 All User")
    if users:
        st.dataframe(df_users, use_container_width=True)

        st.download_button(
            "⬇️ Download Users (CSV)",
            data=df_users.to_csv(index=False),
            file_name="users_export.csv",
            mime="text/csv"
        )
    else:
        st.info("No users found in the system.")
    st.divider()


           
if __name__ == "__main__":
    main()

