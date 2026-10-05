"""
REST API blueprint. All responses are JSON. Write operations are
protected by JWT + role checks (api_roles_required); public GETs are
open so the storefront-style course catalog can be browsed by anyone.
"""
from flask import Blueprint, request, jsonify, g

import models
from auth import issue_jwt, api_login_required, api_roles_required

bp = Blueprint("api", __name__, url_prefix="/api")


# ---------- Auth ----------

@bp.post("/auth/register")
def register():
    data = request.get_json(silent=True) or {}
    name, email, password = data.get("name"), data.get("email"), data.get("password")
    role = data.get("role", "student")

    if not name or not email or not password:
        return jsonify({"error": "name, email and password are required"}), 400
    if role not in ("student", "instructor"):
        # admins are only created by another admin (see /api/users/<id>/role),
        # never via public self-registration
        role = "student"
    if models.get_user_by_email(email):
        return jsonify({"error": "An account with that email already exists"}), 409

    user_id = models.create_user(name, email, password, role)
    user = models.get_user_by_id(user_id)
    token = issue_jwt(user)
    return jsonify({"token": token, "user": models.public_user(user)}), 201


@bp.post("/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    email, password = data.get("email"), data.get("password")
    user = models.get_user_by_email(email) if email else None
    if not user or not models.verify_password(user, password or ""):
        return jsonify({"error": "Invalid email or password"}), 401
    token = issue_jwt(user)
    return jsonify({"token": token, "user": models.public_user(user)})


@bp.get("/auth/me")
@api_login_required
def me():
    user = models.get_user_by_id(g.current_user_id)
    return jsonify(models.public_user(user))


# ---------- Courses ----------

@bp.get("/courses")
def list_courses():
    return jsonify(models.list_courses())


@bp.get("/courses/<int:course_id>")
def get_course(course_id):
    course = models.get_course(course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404
    return jsonify(course)


@bp.post("/courses")
@api_roles_required("instructor", "admin")
def create_course():
    data = request.get_json(silent=True) or {}
    title, description = data.get("title"), data.get("description", "")
    if not title:
        return jsonify({"error": "title is required"}), 400
    course_id = models.create_course(title, description, g.current_user_id)
    return jsonify(models.get_course(course_id)), 201


def _can_manage_course(course):
    return g.current_user_role == "admin" or course["instructor_id"] == g.current_user_id


@bp.put("/courses/<int:course_id>")
@api_roles_required("instructor", "admin")
def update_course(course_id):
    course = models.get_course(course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404
    if not _can_manage_course(course):
        return jsonify({"error": "Forbidden: not your course"}), 403
    data = request.get_json(silent=True) or {}
    title = data.get("title", course["title"])
    description = data.get("description", course["description"])
    models.update_course(course_id, title, description)
    return jsonify(models.get_course(course_id))


@bp.delete("/courses/<int:course_id>")
@api_roles_required("instructor", "admin")
def delete_course(course_id):
    course = models.get_course(course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404
    if not _can_manage_course(course):
        return jsonify({"error": "Forbidden: not your course"}), 403
    models.delete_course(course_id)
    return jsonify({"status": "deleted"})


# ---------- Lessons ----------

@bp.get("/courses/<int:course_id>/lessons")
def list_lessons(course_id):
    if not models.get_course(course_id):
        return jsonify({"error": "Course not found"}), 404
    return jsonify(models.list_lessons(course_id))


@bp.post("/courses/<int:course_id>/lessons")
@api_roles_required("instructor", "admin")
def create_lesson(course_id):
    course = models.get_course(course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404
    if not _can_manage_course(course):
        return jsonify({"error": "Forbidden: not your course"}), 403
    data = request.get_json(silent=True) or {}
    title, content = data.get("title"), data.get("content", "")
    order_index = data.get("order_index", 0)
    if not title:
        return jsonify({"error": "title is required"}), 400
    lesson_id = models.create_lesson(course_id, title, content, order_index)
    return jsonify(models.get_lesson(lesson_id)), 201


@bp.delete("/lessons/<int:lesson_id>")
@api_roles_required("instructor", "admin")
def delete_lesson(lesson_id):
    lesson = models.get_lesson(lesson_id)
    if not lesson:
        return jsonify({"error": "Lesson not found"}), 404
    course = models.get_course(lesson["course_id"])
    if not _can_manage_course(course):
        return jsonify({"error": "Forbidden: not your course"}), 403
    models.delete_lesson(lesson_id)
    return jsonify({"status": "deleted"})


# ---------- Enrollments ----------

@bp.post("/courses/<int:course_id>/enroll")
@api_roles_required("student")
def enroll(course_id):
    if not models.get_course(course_id):
        return jsonify({"error": "Course not found"}), 404
    if models.is_enrolled(g.current_user_id, course_id):
        return jsonify({"error": "Already enrolled"}), 409
    models.enroll_student(g.current_user_id, course_id)
    return jsonify({"status": "enrolled"}), 201


@bp.get("/enrollments/me")
@api_roles_required("student")
def my_enrollments():
    return jsonify(models.list_enrollments_for_student(g.current_user_id))


@bp.get("/courses/<int:course_id>/enrollments")
@api_roles_required("instructor", "admin")
def course_enrollments(course_id):
    course = models.get_course(course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404
    if not _can_manage_course(course):
        return jsonify({"error": "Forbidden: not your course"}), 403
    return jsonify(models.list_enrollments_for_course(course_id))


@bp.patch("/enrollments/<int:course_id>/progress")
@api_roles_required("student")
def update_progress(course_id):
    data = request.get_json(silent=True) or {}
    progress = data.get("progress")
    if progress is None or not (0 <= int(progress) <= 100):
        return jsonify({"error": "progress must be an integer 0-100"}), 400
    if not models.is_enrolled(g.current_user_id, course_id):
        return jsonify({"error": "Not enrolled in this course"}), 403
    models.update_progress(g.current_user_id, course_id, progress)
    return jsonify({"status": "updated", "progress": progress})


# ---------- Users (admin only) ----------

@bp.get("/users")
@api_roles_required("admin")
def list_users():
    return jsonify(models.list_users())


@bp.patch("/users/<int:user_id>/role")
@api_roles_required("admin")
def change_role(user_id):
    data = request.get_json(silent=True) or {}
    role = data.get("role")
    if role not in ("admin", "instructor", "student"):
        return jsonify({"error": "role must be admin, instructor or student"}), 400
    if not models.get_user_by_id(user_id):
        return jsonify({"error": "User not found"}), 404
    models.update_user_role(user_id, role)
    return jsonify(models.public_user(models.get_user_by_id(user_id)))
