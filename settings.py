import streamlit as st
import bcrypt
import os
from utils.models import update_user_info, change_password, update_profile_pic, get_user_settings

UPLOAD_DIR = "profile_picture"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def settings_page(user_id,role):
    st.set_page_config(page_title="EduShield | ⚙️ Account Settings", page_icon="images/Edushield_Icon1.png", layout="wide")

    st.title("⚙️ Account Settings")
    st.divider()
    user = get_user_settings(user_id)
    full_name, email, level, profile_pic = user
    
    # Profile Picture
    st.subheader("🖼️ Profile Picture")
    if profile_pic and os.path.exists(profile_pic):
        st.image(profile_pic, width=120, caption="Current Picture")
    uploaded = st.file_uploader("Upload new profile picture", type=["jpg","png","jpeg"])
    if uploaded:
        file_path = os.path.join(UPLOAD_DIR, f"user_{user_id}_{uploaded.name}")
        with open(file_path, "wb") as f:
            f.write(uploaded.getbuffer())
        update_profile_pic(user_id, file_path)
        st.success("✅ Profile picture updated!")

    st.markdown("---")

    # Personal Info
    st.subheader("👤 Personal Information")
    new_name = st.text_input("Full Name", value=full_name)
    new_email = st.text_input("Email", value=user["email"])

    if role == 'student':
        level_option =['ND1','ND2','HND1','HND2']
        new_level = st.selectbox("Level",level_option)
        # new_level = st.text_input("Level", value=level if level else "")
    else:
        new_level= None

    if st.button("Update Info"):
        update_user_info(user_id, new_name,new_email,new_level)
        st.success("✅ Personal info updated!")

    st.markdown("---")

    # Change Password
    st.subheader("🔑 Change Password")
    old_pw = st.text_input("Current Password", type="password")
    new_pw = st.text_input("New Password", type="password")
   
    st.divider()


def main():
    u = st.session_state['user']
    user_id = u['id']
    role = u['role']
    settings_page(user_id,role)


main()
