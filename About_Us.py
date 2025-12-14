import streamlit as st


def about_page():
    # Title + Hero Section
    st.set_page_config(page_title="EduShield | ℹ️ About Us", page_icon="images/Edushield_Icon1.png", layout="wide")
    
    st.title("ℹ️ About Us")
    st.caption("'Everything you need to know about EduShield'")
    st.divider()

    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("images/logo.png", caption="EduShield", width=180)
    with col2:
        st.markdown(
            """
            EduShield is a **Secure Academic Management System** designed to provide institutions 
            with a safe, reliable, and user-friendly platform for managing academic records.  

            Our goal is to ensure that students, lecturers, and administrators can seamlessly access academic data 
            while maintaining the highest standards of **security and privacy**.
            """
        )

    st.markdown("---")

    # Mission
    st.header("🎯 Our Mission")
    st.info(
        """
        To create a **secure, efficient, and transparent academic management system** that empowers institutions 
        to protect sensitive data, enhance student performance, and streamline academic operations.
        """
    )

    st.markdown("---")

    # Who We Serve
    st.header("👥 Who We Serve")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("🎓 Students")
        st.markdown("Access **attendance, results, GPA predictions, and exam eligibility** in one place.")

    with col2:
        st.subheader("👨‍🏫 Lecturers")
        st.markdown("Easily **manage courses, upload resources, and monitor student performance.**")

    with col3:
        st.subheader("🏛️ Administrators")
        st.markdown("Control **system settings, allocate courses, and ensure institutional compliance.**")

    st.markdown("---")

    # Why Choose EduShield
    st.header("🔒 Why Choose EduShield?")
    col1, col2 = st.columns(2)

    with col1:
        st.success("✅ **Data Security** – Role-based access control")
        st.success("✅ **Transparency** – Real-time academic progress tracking")
        st.success("✅ **Efficiency** – Automated GPA prediction and attendance monitoring")

    with col2:
        st.success("✅ **Scalability** – Grows with institutions of any size")
        st.success("✅ **Reliability** – Modern, stable, and high-performance system")
        st.success("✅ **User-Friendly** – Simple and intuitive for all roles")

    st.markdown("---")

    # Core Values
    st.header("🌟 Core Values")
    st.markdown(
        """
        - **Integrity** 🕊️ – Protecting academic data with honesty and transparency  
        - **Innovation** 💡 – Leveraging technology to transform education  
        - **Collaboration** 🤝 – Bridging the gap between students, lecturers, and admins  
        - **Excellence** 🏆 – Empowering institutions and students to achieve more  
        """
    )

    st.markdown("---")

    # Vision
    st.header("📌 Our Vision")
    st.info(
        "To become a **trusted global platform** that redefines how academic institutions handle and secure sensitive data "
        "while promoting **academic excellence** everywhere."
    )

    st.markdown("---")

    # Contact Section
    st.header("📞 Contact & Support")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("📧 **Email**: support@edushield.com")
        st.markdown("🌐 **Website**: www.edushield.com")
    with col2:
        st.markdown("📍 **Headquarters**: Lagos, Nigeria")
        st.markdown("☎️ **Phone**: +234 800 123 4567")

    # Divider
    st.markdown("---")

    # 🌟 Final Year Project Info
    st.markdown(
        """
        <div style="text-align:center; background-color:#f0f2f6; padding:15px; border-radius:10px; margin-top:30px;">
            <h4>🎓 Final Year Project</h4>
            <p style="margin:5px 0;">Designed and Developed by</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col3, col4, col5 = st.columns(3, border=True)
            
    with col3:
        st.image("static/az8.jpg")
        st.markdown("""
        <div style="text-align:center; padding: 5px;">
            <p style="font-size:15px; color:gray;">  
                <b>ABDULAKEEM ABDULAZEEZ ARAMIDE</b>
            </p>
            <p style="font-size:15px; color:gray;">  
                <b>(23/105/01/F/0002)</b>
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.image("static/ben1.jpg")
        st.markdown("""
        <div style="text-align:center; padding: 5px;">
            <p style="font-size:15px; color:gray;">  
                <b>JOSEPH BENJAMIN OLUWATEMITOPE</b>
            </p>
            <p style="font-size:15px; color:gray;">  
                <b>(23/105/01/F/0143)</b>
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col5:
        st.image("static/upward1.jpg")
        st.markdown("""
        <div style="text-align:center; padding: 5px;">
            <p style="font-size:15px; color:gray;">  
                <b>FADEMINE OLAKUNLE SAMUEL</b>
            </p>
            <p style="font-size:15px; color:gray;">  
                <b>(23/105/01/F/0145)</b>
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(
        """
        <div style="text-align:center; background-color:#f0f2f6; padding:15px; border-radius:10px; margin-top:30px;">
            <p style="margin:5px 0;">Department of Computer Science,</p>
            <p style="margin:5px 0;">Moshood Abiola Polytechnic, Abeokuta, Ogun State, Nigeria.</b></p>
            <p style="color:gray; font-size:12px; margin-top:10px;">Session 2024/2025</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")
    st.caption("© 2025 EduShield | All Rights Reserved | Privacy Policy | Terms of Service")


about_page()
