# EduSphere — E-Learning Platform

A full-stack e-learning platform built with **Python, Flask, MySQL, HTML, CSS, JavaScript**,
featuring session + JWT authentication, role-based access control (admin /
instructor / student), and a REST API backing both the web UI and any
external client.

## Features

- **Authentication** — register/login with hashed passwords (Werkzeug),
  session cookies for the web app, and JWTs for the REST API.
- **Role-based access control** — `admin`, `instructor`, and `student` roles
  each see a different dashboard and have different API permissions,
  enforced by decorators (`login_required`, `roles_required`,
  `api_roles_required`).
- **REST API** (`/api/...`) — full CRUD for courses and lessons,
  enrollment, progress tracking, and admin user management. See
  [API reference](#api-reference) below.
- **Responsive front end** — server-rendered HTML/CSS with vanilla JS
  calling the REST API for dynamic actions (enroll, create course,
  add lesson, update progress, change a user's role) without full
  page reloads.
- **MySQL-ready** — data access goes through a single `db.py`
  abstraction so the app runs on zero-setup SQLite out of the box, or
  on MySQL in production by flipping one config flag.

## Project structure

```
elearning_platform/
├── app.py                 # Flask application factory / entry point
├── config.py               # Configuration (DB backend, secrets)
├── db.py                   # DB abstraction: SQLite or MySQL (PyMySQL)
├── models.py                # Data-access layer (SQL queries)
├── auth.py                  # Session + JWT auth, RBAC decorators
├── main.py                  # Blueprint: server-rendered pages
├── api.py                   # Blueprint: JSON REST API
├── seed.py                  # Creates demo admin/instructor/student + course
├── schema_sqlite.sql        # Auto-applied SQLite schema
├── schema_mysql.sql         # MySQL schema (run manually, see below)
├── requirements.txt
├── templates/                # Jinja2 templates
└── static/css/style.css, static/js/main.js
```

## Quick start (SQLite, no setup required)

```bash
cd elearning_platform
python -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt

python seed.py          # creates demo users + a sample course
python app.py            # runs on http://localhost:5000
```

Demo logins (printed by `seed.py`):

| Role       | Email               | Password    |
|------------|---------------------|-------------|
| admin      | admin@demo.com      | password123 |
| instructor | instructor@demo.com | password123 |
| student    | student@demo.com    | password123 |

The SQLite database file (`elearning.db`) is created automatically the
first time the app runs — nothing else to configure.

## Switching to MySQL

1. Create the schema:
   ```bash
   mysql -u root -p < schema_mysql.sql
   ```
2. Set environment variables (or edit the defaults in `config.py`):
   ```bash
   export DB_BACKEND=mysql
   export MYSQL_HOST=localhost
   export MYSQL_USER=root
   export MYSQL_PASSWORD=yourpassword
   export MYSQL_DB=elearning_platform
   ```
3. Run as usual: `python app.py`. Every route and model works
   unchanged — only `db.py`'s connection function differs.

## Roles & permissions

| Action                         | Public | Student | Instructor | Admin |
|---------------------------------|:---:|:---:|:---:|:---:|
| Browse course catalog            | ✅ | ✅ | ✅ | ✅ |
| Register / log in                | ✅ | — | — | — |
| Enroll in a course                |  | ✅ | | |
| Track lesson progress             |  | ✅ | | |
| Create/edit/delete own course     |  |  | ✅ | ✅ (any course) |
| Add/delete lessons on own course  |  |  | ✅ | ✅ (any course) |
| View a course's enrolled students |  |  | ✅ (own) | ✅ |
| List all users / change roles     |  |  |  | ✅ |

## API reference

All endpoints are under `/api`. Protected endpoints require
`Authorization: Bearer <token>` (obtained from `/api/auth/login` or
`/api/auth/register`; the web dashboards also embed a token
automatically for their own JS to use).

| Method | Endpoint                              | Access                | Description |
|--------|-----------------------------------------|------------------------|--------------|
| POST   | `/api/auth/register`                     | Public                 | Create an account (student/instructor) |
| POST   | `/api/auth/login`                        | Public                 | Get a JWT |
| GET    | `/api/auth/me`                           | Any logged-in user      | Current user info |
| GET    | `/api/courses`                           | Public                 | List all courses |
| GET    | `/api/courses/<id>`                      | Public                 | Course details |
| POST   | `/api/courses`                           | Instructor/Admin        | Create a course |
| PUT    | `/api/courses/<id>`                      | Owner instructor/Admin  | Update a course |
| DELETE | `/api/courses/<id>`                      | Owner instructor/Admin  | Delete a course |
| GET    | `/api/courses/<id>/lessons`               | Public                 | List lessons |
| POST   | `/api/courses/<id>/lessons`               | Owner instructor/Admin  | Add a lesson |
| DELETE | `/api/lessons/<id>`                       | Owner instructor/Admin  | Delete a lesson |
| POST   | `/api/courses/<id>/enroll`                | Student                | Enroll in a course |
| GET    | `/api/enrollments/me`                     | Student                | My enrolled courses |
| GET    | `/api/courses/<id>/enrollments`           | Owner instructor/Admin  | Students enrolled in a course |
| PATCH  | `/api/enrollments/<id>/progress`          | Student (enrolled)      | Update my progress (0-100) |
| GET    | `/api/users`                             | Admin                  | List all users |
| PATCH  | `/api/users/<id>/role`                    | Admin                  | Change a user's role |

Example:

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "instructor@demo.com", "password": "password123"}'
```

## Notes on scalability / design decisions

- **Connection-per-request** via Flask's `g` object, closed in a
  `teardown_appcontext` handler, avoids leaking connections under load.
- **Parameterized queries** everywhere (no string-built SQL) prevent
  SQL injection and let the exact same query run against SQLite or
  MySQL by swapping only the placeholder style in `db.py`.
- **Stateless API auth (JWT)** means the REST API can sit behind a
  load balancer with multiple app instances with no shared session
  store required, while the web UI still gets the simplicity of
  cookie sessions.
- **Indexes**: `users.email` is unique (fast login lookups),
  `enrollments (student_id, course_id)` is unique (prevents duplicate
  enrollment and speeds up "is this student enrolled?" checks).
