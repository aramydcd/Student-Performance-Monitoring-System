import bcrypt
from .db import get_conn

def get_user_by_email(email:str):
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM users WHERE email=? AND is_active=1", (email,))
        return cur.fetchone()

def verify_password(pwd:str, password_hash:bytes)->bool:
    try:
        return bcrypt.checkpw(pwd.encode(), password_hash)
    except Exception:
        return False
