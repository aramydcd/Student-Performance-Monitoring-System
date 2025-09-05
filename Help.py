import streamlit as st
from utils.models import save_support_ticket,view_support_tickets
from utils.rbac import allow_roles


@allow_roles("student","lecturer","admin")
def help_support_page():
    st.set_page_config(page_title="EduShield | 🆘 Help & Support", page_icon="images/Edushield_Icon1.png", layout="wide")
    u = st.session_state["user"]

    st.title("🆘 Help & Support")
    st.caption("Need help? You’re in the right place!")

    # Quick Help
    st.header("💡 Quick Help")
    with st.expander("🔑 I forgot my password"):
        st.markdown("""
        - Click on the **Login Page**.  
        - Select **Forgot Password** (if enabled).  
        - Or, contact your **Admin** to reset your password.  
        """)
    with st.expander("📚 How do I register for a course?"):
        st.markdown("""
        - Navigate to **Course Registration** in your dashboard.  
        - Select available courses for your level and session.  
        - Click **Register** to confirm.  
        """)
    with st.expander("👨‍🏫 How can lecturers upload resources?"):
        st.markdown("""
        - Go to **My Courses** → select a course.  
        - Use the **Upload Resource** option.  
        - Students will be notified automatically.  
        """)
    with st.expander("📊 Where can students see results?"):
        st.markdown("""
        - Go to **Results** section in your dashboard.  
        - Results include **tests, assignments, and exam scores**.  
        - GPA prediction is automatically calculated.  
        """)

    st.markdown("---")

    # Contact Support
    st.header("📞 Contact Support")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📧 Email Support")
        st.markdown("support@edushield.com")

        st.subheader("☎️ Phone")
        st.markdown("+234 800 123 4567")

    with col2:
        st.subheader("🌐 Live Chat")
        st.markdown("Available 9am – 6pm, Mon–Fri (Coming soon 🚀)")

        st.subheader("📍 Office Address")
        st.markdown("EduShield HQ, Lagos, Nigeria")

    st.markdown("---")

    if u['role'] in ['student','lecturer']:
        # Feedback
        st.header("📝 Send Us Feedback")
        with st.form("feedback_form"):
            name = st.text_input("Your Name")
            email = st.text_input("Your Email")
            message = st.text_area("How can we help?")
            submitted = st.form_submit_button("Submit")

            if submitted:
                if not name or not email or not message:
                    st.error("⚠️ Please fill in all fields before submitting.")
                else:
                    save_support_ticket(name, email, message)
                    st.success("✅ Thank you for your feedback! Our support team will get back to you soon.")

    if u['role'] == 'admin':
        st.title("📩 Support Tickets")
        rows = view_support_tickets()
        # st.dataframe(rows)
        for row in rows:
            with st.expander(f"**Ticket ID:** {row[0]}"):
                st.write(f"**Name:** {row[1]}")
                st.write(f"**Email:** {row[2]}")
                st.write(f"**Message:** {row[3]}")
                st.write(f"**Status:** {row[4]}")
                st.write(f"**Created At:** {row[5]}")
              

    # Footer
    st.markdown("---")
    st.caption("© 2025 EduShield | Help & Support Team")


help_support_page()
