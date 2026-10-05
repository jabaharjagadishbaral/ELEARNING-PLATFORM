"""
Thin database abstraction layer.

Every route/model talks to the database only through query() and
execute() below, using MySQL-style "%s" placeholders. That keeps the
whole app portable between SQLite (used out of the box, no setup
required) and MySQL (production, via PyMySQL) without touching any
business logic.
"""
import sqlite3
from flask import current_app, g


def _sqlite_connect():
    path = current_app.config["SQLITE_PATH"]
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _mysql_connect():
    import pymysql
    import pymysql.cursors

    cfg = current_app.config
    return pymysql.connect(
        host=cfg["MYSQL_HOST"],
        port=cfg["MYSQL_PORT"],
        user=cfg["MYSQL_USER"],
        password=cfg["MYSQL_PASSWORD"],
        database=cfg["MYSQL_DB"],
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


def get_db():
    if "db" not in g:
        backend = current_app.config["DB_BACKEND"]
        g.db = _mysql_connect() if backend == "mysql" else _sqlite_connect()
        g.db_backend = backend
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def _adapt_sql(sql, backend):
    """Translate MySQL-style %s placeholders to sqlite's ? style."""
    if backend == "sqlite":
        return sql.replace("%s", "?")
    return sql


def query(sql, params=(), one=False):
    """Run a SELECT and return a list of dict-like rows (or one row)."""
    db = get_db()
    backend = g.db_backend
    sql = _adapt_sql(sql, backend)
    if backend == "mysql":
        with db.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
    else:
        cur = db.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
    if one:
        return rows[0] if rows else None
    return rows


def execute(sql, params=()):
    """Run an INSERT/UPDATE/DELETE, commit, and return the new row id."""
    db = get_db()
    backend = g.db_backend
    sql = _adapt_sql(sql, backend)
    if backend == "mysql":
        with db.cursor() as cur:
            cur.execute(sql, params)
            new_id = cur.lastrowid
        db.commit()
    else:
        cur = db.execute(sql, params)
        db.commit()
        new_id = cur.lastrowid
    return new_id


def init_app(app):
    app.teardown_appcontext(close_db)


def init_schema():
    """Create tables if they don't exist yet (SQLite dev convenience)."""
    import os

    if current_app.config["DB_BACKEND"] != "sqlite":
        return  # MySQL: run schema_mysql.sql manually, see README
    path = os.path.join(os.path.dirname(__file__), "schema_sqlite.sql")
    with open(path, "r") as f:
        sql_script = f.read()
    db = get_db()
    db.executescript(sql_script)
    db.commit()
