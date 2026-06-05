import os
import tempfile
from datetime import timedelta


def normalize_mysql_url(database_url):
    if database_url and database_url.startswith("mysql://"):
        return database_url.replace("mysql://", "mysql+pymysql://", 1)
    return database_url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 26214400))
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "static/uploads")
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL")
    ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH")
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
    MAX_PHOTOS_PER_LISTING = 5
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_REFRESH_EACH_REQUEST = True


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DEV_DATABASE_URL", "sqlite:///kiraya_haa_dev.db"
    )


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = normalize_mysql_url(
        os.environ.get("PROD_DATABASE_URL") or os.environ.get("MYSQL_URL")
    )
    if not SQLALCHEMY_DATABASE_URI and os.environ.get("VERCEL"):
        temp_db_path = os.path.join(tempfile.gettempdir(), "kiraya_haa_vercel.db")
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{temp_db_path.replace(os.sep, '/')}"
        VERCEL_SQLITE_FALLBACK = True
    else:
        VERCEL_SQLITE_FALLBACK = False
