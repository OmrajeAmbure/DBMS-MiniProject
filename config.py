import os
import psycopg2
from urllib.parse import urlparse

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://sms_db_erov_user:uPwjVlCSQF55yJylsvTCmr5d6aCiGCg1@dpg-d481fgi4d50c738g01j0-a/sms_db_erov")

if DATABASE_URL:
    result = urlparse(DATABASE_URL)
    DB_CONFIG = {
        "host": result.hostname,
        "user": result.username,
        "password": result.password,
        "database": result.path[1:],  # remove leading slash
        "port": result.port,
        "sslmode": "require"
    }
else:
    DB_CONFIG = {
        "host": os.environ.get("DB_HOST", "localhost"),
        "user": os.environ.get("DB_USER", "root"),
        "password": os.environ.get("DB_PASS", "Omraje@27"),
        "database": os.environ.get("DB_NAME", "sms_db"),
        "port": 5432
    }

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-dev-secret-change-me")
