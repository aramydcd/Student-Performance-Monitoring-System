import sqlite3
from .db import get_conn

def list_courses_for_level(level:str):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM courses WHERE level=? AND is_active=1 ORDER BY code", (level,)).fetchall()

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
        SELECT u.id, u.full_name, u.email
        FROM enrollments e JOIN users u ON u.id=e.student_id
        WHERE e.course_id=? AND e.session=? AND e.semester=?
        ORDER BY u.full_name
        """,(course_id,session,semester)).fetchall()
    


def all_users():
    with get_conn() as conn:
        cur = conn.execute("SELECT email, full_name, role, level, is_active FROM users ORDER BY role, full_name")
        
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
            "Level": rowdict.get("level"),
            "Status": "Active ✅" if rowdict.get("is_active") == 1 else "Not Active ❌",
        })

    return results

def create_user(email, name, role, pw_hash, level):
    with get_conn() as conn:
        conn.execute("INSERT INTO users (email, full_name, role, password_hash, level) VALUES (?,?,?,?,?)",
                     (email, name, role, pw_hash, level))

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





def list_courses_for_level(level: str):
    """
    Returns all courses available for a level.
    """
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM courses WHERE level=? AND is_active=1 ORDER BY code", (level,))
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]

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
def add_course(code: str, title: str, units: int, level: str):
    """
    Adds a new course to the courses table.
    """
    with get_conn() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO courses (code, title, units, level)
            VALUES (?, ?, ?, ?)
        """, (code, title, units, level))
        conn.commit()
