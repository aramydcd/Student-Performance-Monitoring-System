import sqlite3
import os
import bcrypt
from .db import get_conn

    
def list_courses_for_level(level: str):
    """
    Returns all courses available for a level.
    """
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM courses WHERE level=? AND is_active=1 ORDER BY code", (level,))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]

def enroll_student(student_id:int, course_id:int, session:str, semester:str):
    with get_conn() as conn:
        conn.execute("""INSERT OR IGNORE INTO enrollments (student_id,course_id,session,semester)
                        VALUES (?,?,?,?)""", (student_id,course_id,session,semester))

def lecturer_pick_course(lecturer_id:int, course_id:int, session:str, semester:str):
    with get_conn() as conn:
        conn.execute("""INSERT OR IGNORE INTO lecturer_courses (lecturer_id,course_id,session,semester)
                        VALUES (?,?,?,?)""", (lecturer_id,course_id,session,semester))
        
def student_enrollments(student_id: int, session: str, semester: str):
    """
    Returns a list of dicts with friendly keys for the student's enrollments.
    Works whether the DB returns sqlite3.Row (mapping) or plain tuples.
    """
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT e.id, e.session, e.semester, e.created_at,
                   c.code, c.title, c.units
            FROM enrollments e
            JOIN courses c ON c.id = e.course_id
            WHERE e.student_id=? AND e.session=? AND e.semester=?
            ORDER BY c.code
        """, (student_id, session, semester))

        rows = cur.fetchall()
        # Column names from the cursor description
        cols = [d[0] for d in cur.description]  # e.g. ["id","session","semester","created_at","code","title","units"]

    results = []
    for r in rows:
        # Convert row to a dict in a safe way:
        if isinstance(r, sqlite3.Row):
            rowdict = dict(r)                 # sqlite3.Row supports mapping -> dict(row) works
        else:
            # If r is a tuple, pair values with column names
            rowdict = dict(zip(cols, r))

        results.append({
            "Course Code": rowdict.get("code"),
            "Course Title": rowdict.get("title"),
            "Course Units": rowdict.get("units"),
            "Session": rowdict.get("session"),
            "Semester": rowdict.get("semester"),
            "Date Enrolled": rowdict.get("created_at")
        })

    return results


def drop_student_course(student_id: int, course_code: str, session: str, semester: str):
    """
    Remove a student's enrollment for a given course (by course_code),
    session, and semester.
    """
    with get_conn() as conn:
        cur = conn.execute("""
            DELETE FROM enrollments
            WHERE student_id=? AND session=? AND semester=?
              AND course_id = (SELECT id FROM courses WHERE code=?)
        """, (student_id, session, semester, course_code))
        conn.commit()
        return cur.rowcount  # number of rows deleted (0 or 1)
    

def mark_attendance(course_id:int, student_id:int, class_date:str, present:bool, marked_by:int):
    with get_conn() as conn:
        conn.execute("""INSERT OR REPLACE INTO attendance (course_id,student_id,class_date,present,marked_by)
                        VALUES (?,?,?,?,?)""",
                     (course_id,student_id,class_date, 1 if present else 0, marked_by))

def upsert_score(course_id:int, student_id:int, component:str, score:float, lecturer_id:int):
    with get_conn() as conn:
        # REPLACE will overwrite same (course,student,component,created_at is new)
        conn.execute("""INSERT INTO scores (course_id,student_id,component,score,entered_by)
                        VALUES (?,?,?,?,?)""", (course_id,student_id,component,score,lecturer_id))


def get_scores(student_id: int):
    """
    Returns scores grouped by course and component (test, assignment, exam).
    Only pulls fields that actually exist in the DB.
    """
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT c.code, c.title, c.units,
                   s.component, s.score, s.created_at
            FROM scores s
            JOIN courses c ON c.id = s.course_id
            WHERE s.student_id=?
            ORDER BY c.code, s.component
        """, (student_id,))
        
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]

    results = []
    for r in rows:
        if isinstance(r, sqlite3.Row):
            rowdict = dict(r)
        else:
            rowdict = dict(zip(cols, r))

        results.append({
            "Course Code": rowdict.get("code"),
            "Course Title": rowdict.get("title"),
            "Course Units": rowdict.get("units"),
            "Component": rowdict.get("component").title(),
            "Score": rowdict.get("score"),
            "Date Entered": rowdict.get("created_at")
        })

    return results


def percentage_attendance(student_id:int, course_id:int):
    with get_conn() as conn:
        tot = conn.execute("SELECT COUNT(*) as n FROM attendance WHERE student_id=? AND course_id=?",(student_id,course_id)).fetchone()["n"]
        pres = conn.execute("SELECT COUNT(*) as n FROM attendance WHERE student_id=? AND course_id=? AND present=1",(student_id,course_id)).fetchone()["n"]
        return (pres/tot*100.0) if tot else 0.0

def list_students_in_course(course_id:int, session:str, semester:str):
    with get_conn() as conn:
        return conn.execute("""
        SELECT u.full_name, u.email
        FROM enrollments e JOIN users u ON u.id=e.student_id
        WHERE e.course_id=? AND e.session=? AND e.semester=?
        ORDER BY u.full_name
        """,(course_id,session,semester)).fetchall()
    
def get_user_id_by_email(email:str):
    with get_conn() as conn:
        row = conn.execute("""
        SELECT u.id
        FROM users u
        WHERE u.email=? 
        """,(email,)).fetchone()

        return row[0] if row else None



def all_users():
    with get_conn() as conn:
        cur = conn.execute("SELECT email, full_name, role,matric_no, level, is_active FROM users ORDER BY role, full_name")
        
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]

    results = []
    for r in rows:
        # support sqlite3.Row or plain tuples
        rowdict = dict(r) if isinstance(r, sqlite3.Row) else dict(zip(cols, r))

        results.append({
            "Email": rowdict.get("email"),
            "Fullname": rowdict.get("full_name"),
            "Role": rowdict.get("role"),
            "Matric Number": rowdict.get("matric_no"),
            "Level": rowdict.get("level"),
            "Status": "Active ✅" if rowdict.get("is_active") == 1 else "Not Active ❌",
        })

    return results


        
def create_user(full_name, email, role, hashed_pwd, matric_no=None, level=None):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO users (full_name,email,role,password_hash,matric_no,level)
            VALUES (?,?,?,?,?,?)
        """, (full_name,
              email,
              role,
              hashed_pwd,
              matric_no,
              level
            )
        )
        conn.commit()
        cur = conn.execute("SELECT id FROM users WHERE email = ?", (email,))
        user_id = cur.fetchone()[0]
    return user_id

def attendance_summary(student_id: int):

    """
    Return % attendance for each course a student is enrolled in.
    """
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT c.code, c.title,
                   COUNT(*) AS total_classes,
                   SUM(a.present) AS attended
            FROM attendance a
            JOIN courses c ON c.id = a.course_id
            WHERE a.student_id=?
            GROUP BY c.id
            ORDER BY c.code
        """, (student_id,))
        
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]

    results = []
    for r in rows:
        rowdict = dict(r) if isinstance(r, sqlite3.Row) else dict(zip(cols, r))
        total = rowdict["total_classes"]
        attended = rowdict["attended"] or 0
        pct = (attended / total) * 100 if total > 0 else 0

        results.append({
            "Course Code": rowdict["code"],
            "Course Title": rowdict["title"],
            "Attendance %": round(pct, 1)
        })

    return results

def delete_user_by_email(email: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM users WHERE email=?", (email,))
        conn.commit()

def reset_password(email: str, hashed_pwd: bytes):
    with get_conn() as conn:
        conn.execute("UPDATE users SET password_hash=? WHERE email=?", (hashed_pwd, email))
        conn.commit()


def get_user_by_matric(matric_no: str):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE matric_no=?", (matric_no,)).fetchone()


def get_attendance(student_id: int):
    """
    Return attendance records for a student with course info and the name
    of the user who marked the attendance (if available).
    """
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT a.id, c.code, c.title, a.class_date, a.present,
                   u.full_name AS marked_by
            FROM attendance a
            JOIN courses c ON c.id = a.course_id
            LEFT JOIN users u ON u.id = a.marked_by
            WHERE a.student_id=?
            ORDER BY a.class_date DESC
        """, (student_id,))

        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]

    results = []
    for r in rows:
        # support sqlite3.Row or plain tuples
        rowdict = dict(r) if isinstance(r, sqlite3.Row) else dict(zip(cols, r))

        results.append({
            "Course Code": rowdict.get("code"),
            "Course Title": rowdict.get("title"),
            "Class Date": rowdict.get("class_date"),
            "Status": "Present ✅" if rowdict.get("present") == 1 else "Absent ❌",
            "Marked By": rowdict.get("marked_by") or "Unknown"
        })

    return results

def set_user_active(user_id: int, active: int):
    with get_conn() as conn:
        conn.execute("UPDATE users SET is_active=? WHERE id=?", (active, user_id))
        conn.commit()


def list_resources_for_course(course_code: str):
    """
    Returns all resources uploaded for a course.
    """
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT r.id, r.title, r.description, r.file_path, r.created_at,
                   u.full_name AS lecturer_name
            FROM resources r
            JOIN courses c ON c.id = r.course_id
            JOIN users u ON u.id = r.lecturer_id
            WHERE c.code=?
            ORDER BY r.created_at DESC
        """, (course_code,))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]

# ----------------- Lecturer -----------------
def list_lecturer_courses(lecturer_id: int, session: str, semester: str):
    """
    Returns all courses allocated to a lecturer for a session and semester.
    """
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT c.id, c.code, c.title, c.units
            FROM lecturer_courses lc
            JOIN courses c ON c.id = lc.course_id
            WHERE lc.lecturer_id=? AND lc.session=? AND lc.semester=?
            ORDER BY c.code
        """, (lecturer_id, session, semester))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]

def allocate_course_to_lecturer(lecturer_id: int, course_id: int, session: str, semester: str):
    """
    Allocates a course to a lecturer for a given session and semester.
    """
    with get_conn() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO lecturer_courses (lecturer_id, course_id, session, semester)
            VALUES (?, ?, ?, ?)
        """, (lecturer_id, course_id, session, semester))
        conn.commit()

# ----------------- Admin -----------------
def add_course(code: str, title: str, units: int, level: str, semester = "First", session="2024/2025"):
    """
    Adds a new course to the courses table.
    """
    with get_conn() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO courses (code, title, units, level,semester, session)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (code, title, units, level,semester, session))
        conn.commit()


def save_resource(course_id: int, user_id: int,title, description: str, file):
    """Save uploaded file and insert into DB."""
    os.makedirs("resources", exist_ok=True)
    filepath = os.path.join("resources", file.name)
    with open(filepath, "wb") as f:
        f.write(file.getbuffer())

    # Insert into database
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO resources (course_id, lecturer_id, title, description, file_path)
            VALUES (?, ?, ?, ?, ?)
        """, (course_id, user_id, title, description, filepath))
        conn.commit()



def delete_resource(resource_id: int):
    """Delete resource from DB and file system."""
    with get_conn() as conn:
        cur = conn.execute("SELECT file_path FROM resources WHERE id=?", (resource_id,))
        row = cur.fetchone()
        if row and os.path.exists(row[0]):
            os.remove(row[0])  # remove file
        conn.execute("DELETE FROM resources WHERE id=?", (resource_id,))
        conn.commit()



def list_all_courses(session="2024/2025", semester="First"):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT id, code, title, level, units
            FROM courses
            WHERE session=? AND semester=?
            ORDER BY code
        """, (session, semester)).fetchall()
        # rows are sqlite3.Row (safe to convert now)
        results = [dict(r) for r in rows]
        return results  # return while still inside the with-block

def allocate_course(lecturer_id: int, course_id: int):
    with get_conn() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO course_allocations (lecturer_id, course_id)
            VALUES (?, ?)
        """, (lecturer_id, course_id))
        conn.commit()

def drop_course_allocation(lecturer_id: int, course_id: int):
    with get_conn() as conn:
        conn.execute("""
            DELETE FROM lecturer_courses
            WHERE lecturer_id=? AND course_id=?
        """, (lecturer_id, course_id))
        conn.commit()

def add_notification(title: str, message: str, user_id: int = None, course_id: int = None):
    """Insert a notification for a user, course, or system-wide."""
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO notifications (title, message, user_id, course_id)
            VALUES (?, ?, ?, ?)
        """, (title, message, user_id, course_id))
        conn.commit()

def get_notifications_for_user(user_id: int):
    """Get notifications for a specific student (system + personal + course updates)."""
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT n.id, n.title, n.message, n.created_at, c.code AS course_code
            FROM notifications n
            LEFT JOIN courses c ON c.id = n.course_id
            WHERE n.user_id IS NULL OR n.user_id=? 
               OR n.course_id IN (
                   SELECT course_id FROM enrollments WHERE student_id=?
               )
            ORDER BY n.created_at DESC
        """, (user_id, user_id))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]

def get_all_notifications(limit: int = 200):
    """
    Admin/overview helper: return all notifications (newest first).
    """
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT n.id, n.title, n.message, n.created_at, c.code AS course_code, u.full_name AS target_user
            FROM notifications n
            LEFT JOIN courses c ON c.id = n.course_id
            LEFT JOIN users u ON u.id = n.user_id
            ORDER BY n.created_at DESC
            LIMIT ?
        """, (limit,))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]


def list_all_users():
    """Return minimal user info for admin selectboxes."""
    with get_conn() as conn:
        cur = conn.execute("SELECT id, full_name, email, role FROM users ORDER BY full_name")
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]


def get_user_matric_by_email(email:str):
    with get_conn() as conn:
        row = conn.execute("""
        SELECT u.matric_no
        FROM users u
        WHERE u.email=? 
        """,(email,)).fetchone()

        return row[0] if row else None
    

def list_courses_for_lecturer(lecturer_id: int, session: str = None, semester: str = None):
    """
    Return courses allocated to lecturer. session & semester optional.
    """
    with get_conn() as conn:
        if session and semester:
            cur = conn.execute("""
                SELECT c.id, c.code, c.title
                FROM lecturer_courses lc
                JOIN courses c ON c.id = lc.course_id
                WHERE lc.lecturer_id=? AND lc.session=? AND lc.semester=?
                ORDER BY c.code
            """, (lecturer_id, session, semester))
        else:
            cur = conn.execute("""
                SELECT c.id, c.code, c.title
                FROM lecturer_courses lc
                JOIN courses c ON c.id = lc.course_id
                WHERE lc.lecturer_id=?
                ORDER BY c.code
            """, (lecturer_id,))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]

def get_recent_notifications(user_id: int, limit: int = 3):
    """
    Fetches the most recent notifications for a student.
    Includes system-wide (NULL user_id) and personal ones.
    """
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT id, title, message, created_at
            FROM notifications
            WHERE user_id IS NULL OR user_id=?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, limit))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]


def drop_lecturer_course(lecturer_id, course_code, session, semester):
    """Delete a lecturer's registered course by course code."""
    with get_conn() as conn:
        row = conn.execute("""
            SELECT lc.id 
            FROM lecturer_courses lc
            JOIN courses c ON c.id = lc.course_id
            WHERE lc.lecturer_id=? AND c.code=? AND lc.session=? AND lc.semester=?
        """, (lecturer_id, course_code, session, semester)).fetchone()
        if not row:
            return False
        conn.execute("DELETE FROM lecturer_courses WHERE id=?", (row["id"],))
        conn.commit()
        return True
    
def get_course_ids(id, session, semester):
    with get_conn() as conn:
        mine = conn.execute("""
            SELECT lc.id, c.code, c.title 
            FROM lecturer_courses lc
            JOIN courses c ON c.id=lc.course_id
            WHERE lc.lecturer_id=? AND lc.session=? AND lc.semester=?
            ORDER BY c.code
        """,(id, session, semester)).fetchall()
    return mine



def count_users_by_role(role: str):
    with get_conn() as conn:
        cur = conn.execute("SELECT COUNT(*) FROM users WHERE role=?", (role,))
        return cur.fetchone()[0]

def count_courses():
    with get_conn() as conn:
        cur = conn.execute("SELECT COUNT(*) FROM courses")
        return cur.fetchone()[0]
    
def count_resources():
    with get_conn() as conn:
        cur = conn.execute("SELECT COUNT(*) FROM resources")
        return cur.fetchone()[0]

def get_avg_gpa():
    with get_conn() as conn:
        cur = conn.execute("SELECT AVG(gpa) FROM student_gpa")
        row = cur.fetchone()
        return row[0] if row and row[0] else 0.0

def get_avg_attendance():
    with get_conn() as conn:
        cur = conn.execute("SELECT AVG(present*100.0/total) FROM ( \
            SELECT student_id, course_id, COUNT(*) as total, SUM(present) as present \
            FROM attendance GROUP BY student_id, course_id )")
        row = cur.fetchone()
        return row[0] if row and row[0] else 0.0

def get_system_alerts():
    alerts = []
    # Example rules
    if get_avg_attendance() < 50:
        alerts.append("Low overall attendance detected.")
    if get_avg_gpa() < 2.0:
        alerts.append("Average GPA is below 2.0.")
    return alerts


def get_user_by_email(email: str):
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM users WHERE email=?", (email,))
        return cur.fetchone()


# Map scores to grade points
def score_to_gp(score):
    if score >= 70:
        return 4.0
    elif score >= 60:
        return 3.0
    elif score >= 50:
        return 2.0
    elif score >= 45:
        return 1.0
    else:
        return 0.0

def calculate_gpa(student_id, session, semester):
    with get_conn() as conn:
        # fetch all courses the student enrolled in this session/semester
        rows = conn.execute("""
            SELECT c.id, c.units,
                   COALESCE((
                       SELECT AVG(s.score)
                       FROM scores s
                       WHERE s.course_id = c.id
                         AND s.student_id = e.student_id
                   ), 0) as avg_score
            FROM enrollments e
            JOIN courses c ON c.id = e.course_id
            WHERE e.student_id=? AND e.session=? AND e.semester=?
        """, (student_id, session, semester)).fetchall()

        total_points, total_units = 0, 0
        for r in rows:
            gp = score_to_gp(r["avg_score"])
            total_points += gp * r["units"]
            total_units += r["units"]

        gpa = round(total_points / total_units, 2) if total_units > 0 else 0.0

        # upsert into student_gpa
        conn.execute("""
            INSERT INTO student_gpa (student_id, session, semester, gpa)
            VALUES (?,?,?,?)
            ON CONFLICT(student_id, session, semester)
            DO UPDATE SET gpa=excluded.gpa, created_at=CURRENT_TIMESTAMP
        """, (student_id, session, semester, gpa))
        conn.commit()

        return gpa


def update_is_active(user_id, value):
    with get_conn() as conn:
        conn.execute("UPDATE users SET is_active = ? WHERE id = ?", (value, user_id))
        conn.commit()




# ----------------- Courses Management -----------------
def get_course_by_code(code: str):
    """Fetch a single course by course code."""
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM courses WHERE code=?", (code,))
        return cur.fetchone()

def delete_course(course_id: int):
    """Delete a course by ID (removes allocations and enrollments too)."""
    with get_conn() as conn:
        # Remove enrollments & allocations first (foreign key safety)
        conn.execute("DELETE FROM enrollments WHERE course_id=?", (course_id,))
        conn.execute("DELETE FROM lecturer_courses WHERE course_id=?", (course_id,))
        conn.execute("DELETE FROM resources WHERE course_id=?", (course_id,))
        conn.execute("DELETE FROM scores WHERE course_id=?", (course_id,))
        conn.execute("DELETE FROM attendance WHERE course_id=?", (course_id,))
        conn.execute("DELETE FROM messages WHERE course_id=?", (course_id,))
        conn.execute("DELETE FROM notifications WHERE course_id=?", (course_id,))
        conn.execute("DELETE FROM courses WHERE id=?", (course_id,))
        conn.commit()

def list_course_students(course_id: int, session: str, semester: str):
    """List students enrolled in a specific course."""
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT u.full_name, u.email, u.matric_no, u.level
            FROM enrollments e
            JOIN users u ON u.id = e.student_id
            WHERE e.course_id=? AND e.session=? AND e.semester=?
            ORDER BY u.full_name
        """, (course_id, session, semester))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]

    results = []
    for r in rows:
        # support sqlite3.Row or plain tuples
        rowdict = dict(r) if isinstance(r, sqlite3.Row) else dict(zip(cols, r))

        results.append({
            "Fullname": rowdict.get("full_name"),
            "Email": rowdict.get("email"),
            "Matric Number": rowdict.get("matric_no"),
            "Level": rowdict.get("level"),
        })

    return results

def list_course_lecturers(course_id: int, session: str = "2024/2025", semester: str = "First"):
    """List lecturers teaching a course (with optional session & semester)."""
    with get_conn() as conn:
        if session and semester:
            cur = conn.execute("""
                SELECT u.id, u.full_name, u.email
                FROM lecturer_courses lc
                JOIN users u ON u.id = lc.lecturer_id
                WHERE lc.course_id=? AND lc.session=? AND lc.semester=?
            """, (course_id, session, semester))
        else:
            cur = conn.execute("""
                SELECT u.id, u.full_name, u.email
                FROM lecturer_courses lc
                JOIN users u ON u.id = lc.lecturer_id
                WHERE lc.course_id=?
            """, (course_id,))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]

# ----------------- Resources Management -----------------
def get_resource_by_id(resource_id: int):
    """Fetch a resource by ID."""
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM resources WHERE id=?", (resource_id,))
        return cur.fetchone()

def list_all_resources():
    """List all uploaded resources across courses."""
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT r.id, r.title, r.description, r.file_path, r.created_at,
                   c.code AS course_code, c.title AS course_title,
                   u.full_name AS lecturer_name
            FROM resources r
            JOIN courses c ON c.id = r.course_id
            JOIN users u ON u.id = r.lecturer_id
            ORDER BY r.created_at DESC
        """)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]


import sqlite3

def get_all_lecturers():
    role = "lecturer"
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row  # rows behave like dicts
        cur = conn.execute(
            """
            SELECT email, full_name, role, is_active 
            FROM users u 
            WHERE u.role = ?
            ORDER BY u.full_name
            """,
            (role,)  # must be tuple
        )
        
        rows = cur.fetchall()

    # Build result list more cleanly
    results = [
        {
            "Email": r["email"],
            "Fullname": r["full_name"],
            "Role": r["role"],
            "Status": "Active ✅" if r["is_active"] == 1 else "Not Active ❌",
        }
        for r in rows
    ]

    return results


def get_course_id_by_code(code: str):
    with get_conn() as conn:
        cur = conn.execute("SELECT id FROM courses WHERE code = ?", (code,))
        row = cur.fetchone()
        return row[0] if row else None

# ------------------- PROFILE ------------------------

def update_user_info(user_id, full_name=None, email=None, level=None):
    with get_conn() as conn:
        if full_name:
            conn.execute("UPDATE users SET full_name=? WHERE id=?", (full_name, user_id))
        if level:
            conn.execute("UPDATE users SET level=? WHERE id=?", (level, user_id))
        if email:
            conn.execute("UPDATE users SET email=? WHERE id=?", (email, user_id))

        # conn.execute("""
        #     UPDATE users
        #     SET full_name = ?, email = ?
        #     WHERE id = ?
        # """, (full_name, email, user_id))


def change_password(user_id, old_password, new_password):
    with get_conn() as conn:
        cur = conn.execute("SELECT password_hash FROM users WHERE id=?", (user_id,))
        row = cur.fetchone()
        if not row:
            return False, "User not found."

        stored_hash = row["password_hash"]
        if not bcrypt.checkpw(old_password.encode(), stored_hash):
            return False, "Old password is incorrect."

        new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
        conn.execute("UPDATE users SET password_hash=? WHERE id=?", (new_hash, user_id))
        return True, "Password updated successfully."


def update_profile_pic(user_id, file_path):
    with get_conn() as conn:
        conn.execute("""
            UPDATE users
            SET profile_pic = ?
            WHERE id = ?
        """, (file_path, user_id))


def get_user_profile(user_id: int):
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT id, email, full_name, matric_no, role, level, is_active, profile_pic, created_at
            FROM users
            WHERE id = ?
        """, (user_id,))
        row = cur.fetchone()

    if row is None:
        return None

    # Convert sqlite3.Row → dict
    return dict(row)

# =================== Help and Support ======================
def save_support_ticket(name, email, message):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO support_tickets (name, email, message)
            VALUES (?, ?, ?)
        """, (name, email, message))

def view_support_tickets():
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT id, name, email, message, status, created_at
            FROM support_tickets
            ORDER BY created_at DESC
        """)
        rows = cur.fetchall()

        return rows

# ========================== SETTINGS ====================
def get_user_settings(user_id):
    with get_conn() as conn:
        cur = conn.execute("SELECT full_name, email, level, profile_pic FROM users WHERE id=?", (user_id,))
        return cur.fetchone()
