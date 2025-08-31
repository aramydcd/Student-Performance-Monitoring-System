import streamlit as st
from utils.rbac import allow_roles
from utils.db import get_conn

@allow_roles("student", "lecturer")
def main():
    st.title("💬 Group Messaging (Course)")
    u = st.session_state["user"]

    # --- init a nonce used to "reset" the input widget by changing its key
    if "msg_nonce" not in st.session_state:
        st.session_state.msg_nonce = 0

    # --- load courses (you can later restrict by role/enrollments if you prefer)
    with get_conn() as conn:
        courses = conn.execute(
            "SELECT id, code FROM courses WHERE is_active=1 ORDER BY code"
        ).fetchall()

    if not courses:
        st.warning("No active courses available.")
        return

    course_map = {c["code"]: c["id"] for c in courses}
    code = st.selectbox("📚 Select Course", list(course_map.keys()))
    course_id = course_map[code]

    # --- input with a rotating key so it resets AFTER we send
    input_key = f"msg_text_{st.session_state.msg_nonce}"
    msg_text = st.text_input("✍️ Type your message:", key=input_key)

    # --- send message
    if st.button("Send"):
        body = (st.session_state.get(input_key) or "").strip()
        if not body:
            st.warning("Message cannot be empty.")
        else:
            with get_conn() as conn:
                conn.execute(
                    "INSERT INTO messages (sender_id, course_id, body) VALUES (?,?,?)",
                    (u["id"], course_id, body),
                )
            # rotate the key so the input is recreated empty on next run
            st.session_state.msg_nonce += 1
            st.success("Message sent!")
            st.rerun()

    # --- display thread
    with get_conn() as conn:
        msgs = conn.execute(
            """
            SELECT m.body, m.created_at, u.full_name
            FROM messages m
            JOIN users u ON u.id = m.sender_id
            WHERE m.course_id=?
            ORDER BY m.created_at DESC
            """,
            (course_id,),
        ).fetchall()

    st.subheader("💬 Thread")
    if not msgs:
        st.info("No messages yet for this course.")
    else:
        for m in msgs:
            st.markdown(f"**{m['full_name']}** ({m['created_at']}): {m['body']}")

if __name__ == "__main__":
    main()
