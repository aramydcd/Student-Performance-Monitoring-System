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
    profile_pic TEXT,  -- 🆕 added column
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
  session TEXT DEFAULT '2024/2025',
  semester TEXT NOT NULL DEFAULT 'First',
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
                
CREATE TABLE IF NOT EXISTS resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,              -- resource title (e.g., "Lecture Notes Week 1")
    description TEXT,                 -- optional extra info
    file_path TEXT NOT NULL,          -- file location on disk or URL
    course_id INTEGER NOT NULL,       -- link to course
    lecturer_id INTEGER NOT NULL,     -- who uploaded it
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE,
    FOREIGN KEY(lecturer_id) REFERENCES users(id) ON DELETE SET NULL
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

CREATE TABLE IF NOT EXISTS notifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  message TEXT NOT NULL,
  user_id INTEGER,
  course_id INTEGER,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
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
mkuser(email="admin@example.com",
       name="System Admin",
       role="admin",
       pwd="123456"
       )

mkuser(email="lect1@example.com",
       name="Dr. Ada Lecturer",
       role="lecturer",
       pwd="123456"
       )

mkuser(email="stud1@example.com",
       name="Kemi Masho",
       role="student",
       pwd="123456",
       level="ND1",
       matric_no="23/105//01/F/0001"
       )

mkuser(email="stud2@example.com",
       name="Chidi Nkwa",
       role="student",
       pwd="123456",
       level="ND1",
       matric_no="23/021/01/P/0001"
       )

mkuser(email="stud3@example.com",
       name="Kolawole Uzzy",
       role="student",
       pwd="123456",
       level="ND1",
       matric_no="23/021/01/F/0021"
       )

mkuser(email="stud4@example.com",
       name="Chidinma Kolu Nkwa",
       role="student",
       pwd="123456",
       level="ND1",
       matric_no="23/021/01/P/0101"
       )

mkuser(email="stud5@example.com",
       name="Abdulahi Quadri",
       role="student",
       pwd="123456",
       level="ND1",
       matric_no="23/021/01/F/0025"
       )

# seed courses
courses = [
    ("COM 111","INTRODUCTION To COMPUTING",3,"ND1"),
    ("COM 112","INTRODUCTION TO DIGITAL ELERCTRONUCS",3,"ND1"),
    ("COM 113","INTRODUCTION PROGRAMMING LANGUAGE",3,"ND1"),
    ("COM 114","STATISTICS IN COMPUTING I",3,"ND1"),
    ("COM 115","APPLICATION PACKAGES I",3,"ND1"),
    ("MTH111","LOGIC REASONING",2,"ND1"),
    ("GNS 101","CITIZENSHIP EDUCATION I",2,"ND1"),
    ("GNS 111","COMMUNICATION IN ENGLISH I",2,"ND1"),

]
for code,title,units,level in courses:
    c.execute("INSERT OR IGNORE INTO courses (code,title,units,level) VALUES (?,?,?,?)",
              (code,title,units,level))

conn.commit()
conn.close()
print("Database initialized successfully.")
