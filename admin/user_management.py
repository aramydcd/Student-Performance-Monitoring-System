import streamlit as st
import pandas as pd
import bcrypt,sqlite3
from utils.rbac import allow_roles
from utils.db import get_conn
from utils.models import( create_user,all_users,get_user_by_email,count_users_by_role,
                         delete_user_by_email,reset_password,get_user_by_matric
)



@allow_roles("admin")
def main():
    st.set_page_config(page_title="EduShield | 👥 User Management", page_icon="images/Edushield_Icon1.png", layout="wide")
    st.title("👥 User Management")
    st.caption("👥 'Manage all users — students, lecturers, and admins'")
    st.divider()

    users = all_users()
    if users:
        df_users = pd.DataFrame(users)

    # =============================
    # 1. USER OVERVIEW
    # =============================
    st.subheader("📊 User Overview")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👨‍🎓 Students", count_users_by_role("student"))
    with col2:
        st.metric("👨‍🏫 Lecturers", count_users_by_role("lecturer"))
    with col3:
        st.metric("🛡️ Admin", count_users_by_role("admin"))
    st.divider()

    # === Show all users ===
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

    st.subheader("Admin User Tools")
    # === Add New User ===
    with st.expander("➕ Add New User"):
        col1,col2 = st.columns(2)
        full_name = col1.text_input("👤 Full Name", key="signup_full_name")
        email = col2.text_input("📧 Email", key="signup_email")
        role_display = col1.selectbox("🛠️ Role", ["Student", "Lecturer", "Admin"], key="signup_role")

        role = role_display.lower()  # normalize for DB

        if role == "student":
            matric_no = col2.text_input("Matric Number", key="signup_matric")
            level_options = ["ND1", "ND2", "HND1", "HND2"]
            level = col1.selectbox("🎓 Level", level_options, key="signup_level")
        else:
            matric_no = None
            level = None

        pwd = col2.text_input("🔑 Temporary Password", type="password")

        if st.button("➕ Create User"):
            if not email or not full_name or not role or not pwd:
                st.error("⚠️ Please fill all required fields.")
            elif len(pwd) < 6:
                st.error("🔑 Password must be at least 6 characters.")
                return
            elif get_user_by_email(email):
                st.error("🚨 Email already exists")
                return
            elif role == "student":
                if not matric_no:
                    st.error("🚨 Please, provide matric number")
                    return
                if get_user_by_matric(matric_no):
                    st.error("🚨 Matric number already exists")
                    return
            # ✅ Now handle creation for both students & staff
            hashed = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt())
            user_id = create_user(full_name, email, role, hashed, matric_no, level)
            st.success(f"✅ {role_display} account created for {full_name}")

    # === Reset Password ===
    with st.expander("🔄 Reset Password"):
        reset_email = st.text_input("📧 Email for reset")
        new_pwd = st.text_input("New Password", type="password")

        if st.button("🔄 Reset Password"):
            user = get_user_by_email(reset_email)
            if not user:
                st.error("🚨 No user found with that email")
            elif not new_pwd:
                st.error("⚠️ Please enter a new password")
            else:
                hashed = bcrypt.hashpw(new_pwd.encode(), bcrypt.gensalt())
                reset_password(reset_email, hashed)
                st.success(f"🔄 Password reset for {reset_email}")


    # === Activate / Deactivate User ===
    with st.expander("🚦 Activate / Deactivate User"):
        email = st.text_input("📧 Email")
        action = st.radio("Action", ["Activate", "Deactivate"], horizontal=True)

        if st.button("Apply Action"):
            val = 1 if action=="Activate" else 0
            with get_conn() as conn:
                conn.execute("UPDATE users SET is_active=? WHERE email=?", (val, email))
                conn.commit()
            st.success(f"User with the email - {email} has been {action.lower()}d ✅")

    # === Delete User ===
    with st.expander("🗑️ Delete User Account"):
        del_email = st.text_input("📧 Email to delete")
        if st.button("Delete User"):
            user = get_user_by_email(del_email)
            if not user:
                st.error("🚨 No user found with that email")
            else:
                delete_user_by_email(del_email)
                st.success(f"🗑️ User {del_email} deleted")
                st.rerun()

    st.divider()
    

    # === Extra Functionality ===
    # with st.expander("📊 User Statistics"):
    #     with get_conn() as conn:
    #         stats = conn.execute("""
    #             SELECT role, COUNT(*) as total FROM users GROUP BY role
    #         """).fetchall()
    #     stat_df = pd.DataFrame(stats, columns=["Role","Total"])
    #     st.bar_chart(stat_df.set_index("Role"))

if __name__ == "__main__":
    main()
