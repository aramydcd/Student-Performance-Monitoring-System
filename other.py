from utils.models import get_conn

def create_student_gpa_table():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS student_gpa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                session TEXT NOT NULL,
                semester TEXT NOT NULL,
                gpa REAL NOT NULL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(student_id, session, semester)
            );
        """)
        conn.commit()
        print("✅ student_gpa table created successfully.")

if __name__ == "__main__":
    create_student_gpa_table()















# import sqlite3

# DB_PATH = "secure.db"

# def migrate_courses_fk():
#     with sqlite3.connect(DB_PATH) as conn:
#         conn.executescript("""
#             PRAGMA foreign_keys = off;

#             -- Recreate courses with new schema
#             CREATE TABLE courses (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 code TEXT UNIQUE NOT NULL,
#                 title TEXT NOT NULL,
#                 units INTEGER NOT NULL,
#                 level TEXT NOT NULL,
#                 is_active INTEGER DEFAULT 1,
#                 session TEXT NOT NULL,
#                 semester TEXT NOT NULL
#             );


#             DROP TABLE courses_old;

#             PRAGMA foreign_keys = on;
#         """)
#     print("✅ Migration complete: `courses` now includes session + semester.")



# def check_migaration():
#     with sqlite3.connect(DB_PATH) as c:
#         print("Foreign keys on courses:")
#         cur = c.execute("PRAGMA foreign_key_list(courses);")
#         print(cur.fetchall())

#         print("Foreign key violations:")
#         cur = c.execute("PRAGMA foreign_key_check;")
#         print(cur.fetchall())  

# if __name__ == "__main__":
#     # migrate_courses_fk()
#     check_migaration()
