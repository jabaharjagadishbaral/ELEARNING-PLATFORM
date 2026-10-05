import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    """
    Central app configuration.

    DB_BACKEND controls which database layer db.py uses:
      - "sqlite" (default) -> zero-setup local file DB, great for
        running the project immediately / grading / demos.
      - "mysql"  -> production backend, uses PyMySQL and the schema
        in schema_mysql.sql. Set the MYSQL_* environment variables
        (or edit the defaults below) and switch DB_BACKEND to "mysql".

    The data-access layer (models.py) is written against a single
    thin db.py wrapper, so switching backends does not require
    touching any route or model code.
    """

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-change-me")
    JWT_EXP_MINUTES = int(os.environ.get("JWT_EXP_MINUTES", "120"))

    DB_BACKEND = os.environ.get("DB_BACKEND", "sqlite")  # "sqlite" or "mysql"

    # SQLite settings
    SQLITE_PATH = os.environ.get("SQLITE_PATH", os.path.join(BASE_DIR, "elearning.db"))

    # MySQL settings (used only when DB_BACKEND == "mysql")
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
    MYSQL_DB = os.environ.get("MYSQL_DB", "elearning_platform")
