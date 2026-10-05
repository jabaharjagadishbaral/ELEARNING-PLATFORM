"""
Data-access layer. Thin wrappers around db.query()/db.execute() that
return plain dicts, kept separate from route handlers so the REST API
and the server-rendered views can share the exact same logic.
"""
from werkzeug.security import generate_password_hash, check_password_hash
import db


# ---------- Users ----------

def create_user(name, email, password, role):
    password_hash = generate_password_hash(password)
    return db.execute(
        "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
        (name, email, password_hash, role),
    )


def get_user_by_email(email):
    return db.query("SELECT * FROM users WHERE email = %s", (email,), one=True)


def get_user_by_id(user_id):
    return db.query("SELECT * FROM users WHERE id = %s", (user_id,), one=True)


def verify_password(user, password):
    return check_password_hash(user["password_hash"], password)


def list_users():
    return db.query("SELECT id, name, email, role, created_at FROM users ORDER BY id")


def update_user_role(user_id, role):
    db.execute("UPDATE users SET role = %s WHERE id = %s", (role, user_id))


def public_user(user):
    """Strip the password hash before sending a user out over the API."""
    if not user:
        return None
    return {k: v for k, v in dict(user).items() if k != "password_hash"}


# ---------- Courses ----------

def create_course(title, description, instructor_id):
    return db.execute(
        "INSERT INTO courses (title, description, instructor_id) VALUES (%s, %s, %s)",
        (title, description, instructor_id),
    )


def list_courses():
    return db.query(
        """
        SELECT c.*, u.name AS instructor_name
        FROM courses c JOIN users u ON u.id = c.instructor_id
        ORDER BY c.created_at DESC
        """
    )


def get_course(course_id):
    return db.query(
        """
        SELECT c.*, u.name AS instructor_name
        FROM courses c JOIN users u ON u.id = c.instructor_id
        WHERE c.id = %s
        """,
        (course_id,),
        one=True,
    )


def list_courses_by_instructor(instructor_id):
    return db.query(
        "SELECT * FROM courses WHERE instructor_id = %s ORDER BY created_at DESC",
        (instructor_id,),
    )


def update_course(course_id, title, description):
    db.execute(
        "UPDATE courses SET title = %s, description = %s WHERE id = %s",
        (title, description, course_id),
    )


def delete_course(course_id):
    db.execute("DELETE FROM courses WHERE id = %s", (course_id,))


# ---------- Lessons ----------

def create_lesson(course_id, title, content, order_index):
    return db.execute(
        "INSERT INTO lessons (course_id, title, content, order_index) VALUES (%s, %s, %s, %s)",
        (course_id, title, content, order_index),
    )


def list_lessons(course_id):
    return db.query(
        "SELECT * FROM lessons WHERE course_id = %s ORDER BY order_index, id",
        (course_id,),
    )


def get_lesson(lesson_id):
    return db.query("SELECT * FROM lessons WHERE id = %s", (lesson_id,), one=True)


def delete_lesson(lesson_id):
    db.execute("DELETE FROM lessons WHERE id = %s", (lesson_id,))


# ---------- Enrollments ----------

def enroll_student(student_id, course_id):
    return db.execute(
        "INSERT INTO enrollments (student_id, course_id) VALUES (%s, %s)",
        (student_id, course_id),
    )


def is_enrolled(student_id, course_id):
    row = db.query(
        "SELECT id FROM enrollments WHERE student_id = %s AND course_id = %s",
        (student_id, course_id),
        one=True,
    )
    return row is not None


def list_enrollments_for_student(student_id):
    return db.query(
        """
        SELECT e.*, c.title, c.description, u.name AS instructor_name
        FROM enrollments e
        JOIN courses c ON c.id = e.course_id
        JOIN users u ON u.id = c.instructor_id
        WHERE e.student_id = %s
        ORDER BY e.enrolled_at DESC
        """,
        (student_id,),
    )


def list_enrollments_for_course(course_id):
    return db.query(
        """
        SELECT e.*, u.name AS student_name, u.email AS student_email
        FROM enrollments e JOIN users u ON u.id = e.student_id
        WHERE e.course_id = %s
        ORDER BY e.enrolled_at
        """,
        (course_id,),
    )


def update_progress(student_id, course_id, progress):
    db.execute(
        "UPDATE enrollments SET progress = %s WHERE student_id = %s AND course_id = %s",
        (progress, student_id, course_id),
    )
