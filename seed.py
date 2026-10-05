"""
Populate the database with a demo admin, instructor, student, and a
sample course so you can log in and click around immediately.

    python seed.py
"""
from app import create_app
import models

app = create_app()

DEMO_USERS = [
    ("Alice Admin", "admin@demo.com", "password123", "admin"),
    ("Ivan Instructor", "instructor@demo.com", "password123", "instructor"),
    ("Sam Student", "student@demo.com", "password123", "student"),
]

with app.app_context():
    import db
    db.init_schema()

    created = {}
    for name, email, password, role in DEMO_USERS:
        existing = models.get_user_by_email(email)
        if existing:
            created[role] = existing["id"]
            print(f"already exists: {email}")
            continue
        uid = models.create_user(name, email, password, role)
        created[role] = uid
        print(f"created {role}: {email} / {password}")

    existing_courses = models.list_courses_by_instructor(created["instructor"])
    if not existing_courses:
        course_id = models.create_course(
            "Python for Beginners",
            "A friendly introduction to Python programming.",
            created["instructor"],
        )
        models.create_lesson(course_id, "Setting up Python", "Install Python and run your first script.", 1)
        models.create_lesson(course_id, "Variables & data types", "Numbers, strings, lists, and dictionaries.", 2)
        models.create_lesson(course_id, "Control flow", "if/else statements and loops.", 3)
        print(f"created demo course #{course_id} with 3 lessons")
    else:
        print("demo course already exists")

print("\nDone. Log in with:")
for name, email, password, role in DEMO_USERS:
    print(f"  {role:<11} {email} / {password}")
