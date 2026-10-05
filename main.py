"""
Server-rendered pages. These handle full page loads and session-based
auth; the dynamic bits on each page (enroll button, lesson progress,
admin role changes) call the JSON REST API in api.py via fetch() from
static/js/main.js using the JWT obtained at login.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

import models
from auth import (
    login_required,
    roles_required,
    login_user_session,
    logout_user_session,
    current_user,
    issue_jwt,
)

bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    courses = models.list_courses()
    return render_template("index.html", courses=courses, user=current_user())


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "student")
        if role not in ("student", "instructor"):
            role = "student"

        if not name or not email or not password:
            flash("All fields are required.", "error")
        elif models.get_user_by_email(email):
            flash("An account with that email already exists.", "error")
        else:
            user_id = models.create_user(name, email, password, role)
            user = models.get_user_by_id(user_id)
            login_user_session(user)
            flash("Welcome! Your account has been created.", "success")
            return redirect(url_for("main.dashboard"))
    return render_template("register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = models.get_user_by_email(email)
        if user and models.verify_password(user, password):
            login_user_session(user)
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for("main.dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")


@bp.get("/logout")
def logout():
    logout_user_session()
    flash("You've been logged out.", "success")
    return redirect(url_for("main.index"))


@bp.get("/dashboard")
@login_required
def dashboard():
    user = current_user()
    # Issue a short-lived JWT for this page's own JS to call the REST API with.
    api_token = issue_jwt(user)

    if user["role"] == "admin":
        users = models.list_users()
        courses = models.list_courses()
        return render_template(
            "dashboard_admin.html", user=user, users=users, courses=courses, api_token=api_token
        )
    elif user["role"] == "instructor":
        courses = models.list_courses_by_instructor(user["id"])
        return render_template(
            "dashboard_instructor.html", user=user, courses=courses, api_token=api_token
        )
    else:  # student
        enrollments = models.list_enrollments_for_student(user["id"])
        enrolled_ids = {e["course_id"] for e in enrollments}
        all_courses = models.list_courses()
        available = [c for c in all_courses if c["id"] not in enrolled_ids]
        return render_template(
            "dashboard_student.html",
            user=user,
            enrollments=enrollments,
            available=available,
            api_token=api_token,
        )


@bp.get("/courses/<int:course_id>")
@login_required
def course_detail(course_id):
    user = current_user()
    course = models.get_course(course_id)
    if not course:
        flash("Course not found.", "error")
        return redirect(url_for("main.dashboard"))

    lessons = models.list_lessons(course_id)
    can_manage = user["role"] == "admin" or (
        user["role"] == "instructor" and course["instructor_id"] == user["id"]
    )
    enrolled = user["role"] == "student" and models.is_enrolled(user["id"], course_id)
    api_token = issue_jwt(user)
    return render_template(
        "course_detail.html",
        user=user,
        course=course,
        lessons=lessons,
        can_manage=can_manage,
        enrolled=enrolled,
        api_token=api_token,
    )


@bp.get("/admin/users")
@roles_required("admin")
def admin_users():
    user = current_user()
    users = models.list_users()
    api_token = issue_jwt(user)
    return render_template("admin_users.html", user=user, users=users, api_token=api_token)
