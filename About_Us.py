import sqlite3

conn = sqlite3.connect("SMS/secure.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    lecturer_id INTEGER NOT NULL,  -- references users(id) where role='lecturer'
    title TEXT NOT NULL,
    description TEXT,              -- optional description of the resource
    file_path TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE,
    FOREIGN KEY(lecturer_id) REFERENCES users(id) ON DELETE CASCADE
);
""")

# c.execute("DROP TABLE IF EXISTS resources")

conn.commit()
conn.close()

