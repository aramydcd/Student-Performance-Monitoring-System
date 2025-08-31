import sqlite3, bcrypt

DB_PATH = "secure.db"

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.executescript("""
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  full_name TEXT NOT NULL,
  matric_no TEXT UNIQUE,  
  role TEXT CHECK(role IN ('admin','lecturer','student')) NOT NULL,
  password_hash BLOB NOT NULL,
  level TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  is_active INTEGER DEFAULT 0,
  CONSTRAINT student_matric CHECK (
      (role = 'student' AND matric_no IS NOT NULL AND level IS NOT NULL) OR 
      (role IN ('lecturer','admin') AND matric_no IS NULL AND level IS NULL)
  )
);

CREATE TABLE IF NOT EXISTS courses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  units INTEGER NOT NULL,
  level TEXT NOT NULL,
  is_active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS enrollments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id INTEGER NOT NULL,
  course_id INTEGER NOT NULL,
  session TEXT NOT NULL,
  semester TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE,
  UNIQUE(student_id, course_id, session, semester)
);

CREATE TABLE IF NOT EXISTS lecturer_courses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lecturer_id INTEGER NOT NULL,
  course_id INTEGER NOT NULL,
  session TEXT NOT NULL,
  semester TEXT NOT NULL,
  FOREIGN KEY(lecturer_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE,
  UNIQUE(lecturer_id, course_id, session, semester)
);

CREATE TABLE IF NOT EXISTS attendance (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  course_id INTEGER NOT NULL,
  student_id INTEGER NOT NULL,
  class_date TEXT NOT NULL,
  present INTEGER NOT NULL,
  marked_by INTEGER,
  FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE,
  FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY(marked_by) REFERENCES users(id) ON DELETE SET NULL,
  UNIQUE(course_id, student_id, class_date)
);

CREATE TABLE IF NOT EXISTS scores (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  course_id INTEGER NOT NULL,
  student_id INTEGER NOT NULL,
  component TEXT CHECK(component IN ('test','assignment','exam')) NOT NULL,
  score REAL NOT NULL,
  entered_by INTEGER,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE,
  FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY(entered_by) REFERENCES users(id) ON DELETE SET NULL
);
                
CREATE TABLE IF NOT EXISTS resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    description TEXT,
    file_path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sender_id INTEGER NOT NULL,
  course_id INTEGER NOT NULL,
  body TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(sender_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
);
""")

def mkuser(email, name, role, pwd, level=None, matric_no=None):
    h = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt())
    if role == "student":
        c.execute(
            "INSERT OR IGNORE INTO users (email, full_name, role, password_hash, level, matric_no) VALUES (?,?,?,?,?,?)",
            (email, name, role, h, level, matric_no)
        )
    else:
        c.execute(
            "INSERT OR IGNORE INTO users (email, full_name, role, password_hash, matric_no, level) VALUES (?,?,?,?,?,?)",
            (email, name, role, h, None, None)
        )

# seed users
mkuser("admin@example.com","System Admin","admin","Admin@123")
mkuser("lect1@example.com","Dr. Ada Lecturer","lecturer","Lecturer@123")
mkuser("stud1@example.com","Kemi Student","student","Student@123","ND1","23/105/001")
mkuser("stud2@example.com","Chidi Student","student","Student@123","ND2","28/01/001")

# seed courses
courses = [
    ("CSC101","Introduction to Computing",3,"ND1"),
    ("MTH111","Calculus I",3,"ND1"),
    ("CSC201","Data Structures",3,"ND2"),
]
for code,title,units,level in courses:
    c.execute("INSERT OR IGNORE INTO courses (code,title,units,level) VALUES (?,?,?,?)",
              (code,title,units,level))

conn.commit()
conn.close()
print("Database initialized successfully.")
