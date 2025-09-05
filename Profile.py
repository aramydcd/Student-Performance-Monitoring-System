import streamlit as st
import os
from utils.rbac import allow_roles
from utils.models import update_user_info, change_password, update_profile_pic
from utils.models import get_user_profile


UPLOAD_DIR = "profile_picture"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@allow_roles("lecturer","student", "admin")

def profile_page(user,u):
    st.title("👤 My Profile")
    st.caption("👤 'View and edit your personal info. with ease.")
    st.divider()

    col1,col2 = st.columns(2)
    # Show existing profile picture
    with col1:
        if not user.get("profile_pic"):
            DEFAULT_AVATAR = "static/default_dp.jpg"
            # If no profile picture uploaded, use default avatar
            user["profile_pic"] = DEFAULT_AVATAR
            # st.info("No profile picture uploaded")
            st.image(user["profile_pic"], width=180)
            st.caption("Profile Picture")
        else:
            st.image(user["profile_pic"], width=180)
            st.caption("Profile Picture")
    # === Show personal info ===
    with col2:
        st.subheader("Basic Info.")
        st.markdown(f"Fullname: {u['full_name']}")
        st.markdown(f"Email: {u['email']}")
        if u['role'] == 'student':
            st.markdown(f"Matric Number: {u['matric_no']}")
            st.markdown(f"Level: {u['level']}")
    st.divider()

    tab1,tab2,tab3 = st.tabs(["Update Basic Info.", "Change Password", "Update Profile Picture"])
    # === Update personal info ===
    with tab1:
        st.subheader("Update Personal Info")
        new_name = st.text_input("Full Name", value=user["full_name"])
        new_email = st.text_input("Email", value=user["email"])

        if st.button("Save Info"):
            update_user_info(user["id"], new_name, new_email)
            st.success("Profile updated successfully")

    # === Change password ===
    with tab2:
        st.subheader("Change Password")
        old_pw = st.text_input("Old Password", type="password")
        new_pw = st.text_input("New Password", type="password")

        if st.button("Update Password"):
            ok, msg = change_password(user["id"], old_pw, new_pw)
            if ok:
                st.success(msg)
            else:
                st.error(msg)

    # === Upload profile picture ===
    with tab3:
        st.subheader("Profile Picture")
        col1,col2 = st.columns(2)
        uploaded_file = col1.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])
        if uploaded_file:
            file_path = os.path.join(UPLOAD_DIR, f"user_{user['id']}_{uploaded_file.name}")
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            update_profile_pic(user["id"], file_path)
            col1.success("Profile picture updated")
            with col2:
                st.image(file_path, width=180)
                st.caption("New Profile Picture")
        # st.rerun()
    st.divider()



def main():
    st.set_page_config(page_title="EduShield | 👤 Profile", page_icon="images/Edushield_Icon1.png", layout="wide")

    u = st.session_state["user"]
    # Example: assume current user ID = 3 (from session)
    user_id = u['id']
    user = get_user_profile(user_id)

    if user:
        profile_page(user, u)
    else:
        st.error("User not found")


if "__main__" == __name__:
    main()
