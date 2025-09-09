import streamlit as st
import pandas as pd
from utils.rbac import allow_roles
from utils.models import (
    add_notification,
    get_notifications_for_user,
    get_all_notifications,
    list_all_courses,
    list_all_users,
    list_courses_for_lecturer,
    get_user_matric_by_email,
    get_user_id_by_email
)

@allow_roles("student", "lecturer", "admin")
def main():
    st.set_page_config(page_title="EduShield | 🔔 Notifications", page_icon="images/Edushield_Icon1.png", layout="wide")

    u = st.session_state["user"]
    role = u["role"]
    st.title("🔔 Notifications")
    st.divider()
  
    # ---------- STUDENT VIEW ----------
    if role == "student":
        st.subheader("Your notifications")
        # in-session "read" list (not persisted)
        if "seen_notifications" not in st.session_state:
            st.session_state["seen_notifications"] = []

        # get and optionally filter
        notifs = get_notifications_for_user(u["id"])

        # Filters
        filt = st.selectbox("Filter", ["All", "System", "Course", "Personal"], index=0)
        def keep(n):
            if filt == "All":
                return True
            if filt == "System":
                return (n.get("course_code") is None) and (n.get("user_id") is None)
            if filt == "Course":
                return n.get("course_code") is not None
            if filt == "Personal":
                return n.get("user_id") == u["id"]
            return True

        visible = [n for n in notifs if keep(n) and n["id"] not in st.session_state["seen_notifications"]]

        if not visible:
            st.info("No new notifications.")
        else:
            for n in visible:
                header = f"{n['title']} — {n['created_at'][:19]}"
                with st.expander(header, expanded=False):
                    if n.get("course_code"):
                        st.markdown(f"**Course:** `{n['course_code']}`")
                    st.write(n["message"])
                    cols = st.columns([1,1,4])
                    if cols[0].button("Mark read", key=f"read_{n['id']}"):
                        st.session_state["seen_notifications"].append(n["id"])
                        st.rerun()
                    if cols[1].button("Save (client)", key=f"save_{n['id']}"):
                        # optionally let user save to local file
                        st.download_button(label="Save as .txt", data=n["message"], file_name=f"notification_{n['id']}.txt")

    # ---------- LECTURER / ADMIN VIEW ----------
    else:
        st.subheader("Create a notification")
        user_name = u['full_name']
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Title")
            target = st.selectbox("Target type", ["System (all)", "Course", "User"])
        with col2:
            # If course target: lecturer sees only their courses; admin sees all
            message = st.text_area("Message", height=140)

        course_id = None
        user_id = None

        if target == "Course":
            if role == "lecturer":
                courses = list_courses_for_lecturer(u["id"])
            else:
                courses = list_all_courses()
            if not courses:
                st.info("No courses available to target.")
            else:
                choice = st.selectbox("Select course", [f"{c['code']} - {c['title']}" for c in courses])
                # map back to course_id
                course_id = [c["id"] for c in courses if f"{c['code']} - {c['title']}" == choice][0]

        elif target == "User":
            users = list_all_users()
            if not users:
                st.info("No users found.")
            else:
                # matric_no = 
                choice = st.selectbox("Select user", [f"{u['full_name']} ({u['email']}) ({get_user_matric_by_email(u['email']) if u['role'] == 'student' else u['role'].title()})" for u in users if user_name != u['full_name']])
                choice = choice.replace(")","").split("(")
                # st.markdown(choice)
                user_id = get_user_id_by_email(choice[1])

        if st.button("Send Notification"):
            if not title or not message:
                st.error("Please provide both title and message.")
            else:
                add_notification(title=title, message=message, user_id=user_id, course_id=course_id)
                st.success("Notification created.")
                st.rerun()

        st.markdown("---")
        # st.subheader("Recent notifications (overview)")
        # all_notifs = get_all_notifications(limit=200)
        # if not all_notifs:
        #     st.info("No notifications yet.")
        # else:
        #     df = pd.DataFrame(all_notifs)
        #     # small friendly display
        #     df_display = df[["created_at", "title", "course_code", "target_user", "message"]]
        #     st.dataframe(df_display, use_container_width=True)

        st.subheader("Your notifications")
        # in-session "read" list (not persisted)
        if "seen_notifications" not in st.session_state:
            st.session_state["seen_notifications"] = []
        # get and optionally filter
        notifs = get_notifications_for_user(u["id"])

        # Filters
        filt = st.selectbox("Filter", ["All", "System", "Course", "Personal"], index=0)
        def keep(n):
            if filt == "All":
                return True
            if filt == "System":
                return (n.get("course_code") is None) and (n.get("user_id") is None)
            if filt == "Course":
                return n.get("course_code") is not None
            if filt == "Personal":
                return n.get("user_id") == u["id"]
            return True

        visible = [n for n in notifs if keep(n) and n["id"] not in st.session_state["seen_notifications"]]

        if not visible:
            st.info("No new notifications.")
        else:
            for n in visible:
                header = f"{n['title']} — {n['created_at'][:19]}"
                with st.expander(header, expanded=False):
                    if n.get("course_code"):
                        st.markdown(f"**Course:** `{n['course_code']}`")
                    st.write(n["message"])
                    cols = st.columns([1,1,4])
                    if cols[0].button("Mark read", key=f"read_{n['id']}"):
                        st.session_state["seen_notifications"].append(n["id"])
                        st.rerun()
                    if cols[1].button("Save (client)", key=f"save_{n['id']}"):
                        # optionally let user save to local file
                        st.download_button(label="Save as .txt", data=n["message"], file_name=f"notification_{n['id']}.txt")


    st.divider()

if __name__ == "__main__":
    main()
