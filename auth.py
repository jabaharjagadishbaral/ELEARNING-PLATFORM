"""
Authentication + role-based access control.

Two auth modes are supported side by side:
  - Session cookies for the server-rendered pages (login_required /
    roles_required check flask.session).
  - JWT bearer tokens for the REST API (api_login_required /
    api_roles_required check the Authorization header), so the same
    API can be called by the web pages' own JS or by a totally
    separate client (mobile app, Postman, another service).
"""
from functools import wraps
from datetime import datetime, timedelta, timezone

import jwt
from flask import session, redirect, url_for, flash, request, jsonify, current_app, g

import models


# ---------- Session-based auth (server-rendered pages) ----------

def login_user_session(user):
    session["user_id"] = user["id"]
    session["role"] = user["role"]


def logout_user_session():
    session.clear()


def current_user():
    if "user_id" not in session:
        return None
    return models.get_user_by_id(session["user_id"])


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("main.login"))
        return view(*args, **kwargs)
    return wrapped


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to continue.", "error")
                return redirect(url_for("main.login"))
            if session.get("role") not in roles:
                flash("You don't have permission to view that page.", "error")
                return redirect(url_for("main.dashboard"))
            return view(*args, **kwargs)
        return wrapped
    return decorator


# ---------- JWT auth (REST API) ----------

def issue_jwt(user):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user["id"],
        "role": user["role"],
        "name": user["name"],
        "iat": now,
        "exp": now + timedelta(minutes=current_app.config["JWT_EXP_MINUTES"]),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")


def decode_jwt(token):
    return jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])


def _extract_token():
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[len("Bearer "):]
    return None


def api_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        token = _extract_token()
        if not token:
            return jsonify({"error": "Missing bearer token"}), 401
        try:
            payload = decode_jwt(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        g.jwt_payload = payload
        g.current_user_id = payload["sub"]
        g.current_user_role = payload["role"]
        return view(*args, **kwargs)
    return wrapped


def api_roles_required(*roles):
    def decorator(view):
        @wraps(view)
        @api_login_required
        def wrapped(*args, **kwargs):
            if g.current_user_role not in roles:
                return jsonify({"error": "Forbidden: insufficient role"}), 403
            return view(*args, **kwargs)
        return wrapped
    return decorator
