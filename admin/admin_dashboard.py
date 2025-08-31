import streamlit as st, pandas as pd, bcrypt
from utils.rbac import allow_roles
from utils.models import all_users, create_user

@allow_roles("admin")
def main():
    st.title("🛡️ Admin Panel")
    st.success("🛡️ Welcome to the Admin Dashboard!")

    st.subheader("Users")
    st.dataframe(pd.DataFrame(all_users()))

    with st.expander("Create user"):
        email = st.text_input("Email")
        name = st.text_input("Full name")
        role = st.selectbox("Role", ["student","lecturer","admin"])
        level = st.selectbox("Level (students only)", ["", "ND1","ND2"])
        pwd = st.text_input("Temp Password", type="password")
        if st.button("Create"):
            if not email or not name or not role or not pwd:
                st.error("Please fill all fields.")
            else:
                h = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt())
                create_user(email, name, role, h, level if role=="student" else None)
                st.success("User created.")

if __name__ == "__main__":
    main()
