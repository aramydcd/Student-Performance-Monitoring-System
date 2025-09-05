# import sqlite3
from utils.db import get_conn


# conn = sqlite3.connect("secure.db")
# c = conn.cursor()

# c.execute("ALTER TABLE users ADD COLUMN profile_pic TEXT;")

def create_support_table():
    with get_conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS support_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

# conn.commit()
# conn.close()

create_support_table()

