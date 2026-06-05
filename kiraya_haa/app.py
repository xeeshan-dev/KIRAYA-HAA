import logging
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, render_template
from flask_login import current_user

from blueprints.admin import admin_bp
from blueprints.auth import auth_bp
from blueprints.inquiries import inquiries_bp
from blueprints.listings import listings_bp
from config import DevelopmentConfig, ProductionConfig
from extensions import bcrypt, csrf, db, login_manager, mail
from blueprints.listings.utils import get_photo_url


def create_app():
    load_dotenv(Path(__file__).resolve().parent / ".env")
    app = Flask(__name__)

    env = os.environ.get("FLASK_ENV", "development")
    app.config.from_object(ProductionConfig if env == "production" else DevelopmentConfig)

    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = secrets.token_hex(32)
        app.logger.warning("SECRET_KEY missing; generated a temporary development key.")

    upload_path = Path(app.root_path) / app.config["UPLOAD_FOLDER"]
    upload_path.mkdir(parents=True, exist_ok=True)

    configure_logging(app)
    register_extensions(app)
    register_blueprints(app)
    register_template_helpers(app)
    register_error_handlers(app)
    initialize_vercel_fallback_db(app)

    return app


def configure_logging(app):
    level = logging.INFO if app.config.get("DEBUG") else logging.WARNING
    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")

    if app.config.get("DEBUG"):
        handler = logging.FileHandler(Path(app.root_path) / "kiraya_haa.log")
    else:
        handler = logging.StreamHandler()

    handler.setFormatter(formatter)
    app.logger.setLevel(level)
    app.logger.addHandler(handler)


def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(listings_bp)
    app.register_blueprint(inquiries_bp)
    app.register_blueprint(admin_bp)


def register_template_helpers(app):
    @app.context_processor
    def inject_helpers():
        return {"current_user": current_user, "photo_url": get_photo_url}

    @app.route("/")
    def index():
        return render_template("index.html")


def register_error_handlers(app):
    @app.errorhandler(403)
    def forbidden(error):
        return render_template("error.html", code=403, message="Access denied."), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("error.html", code=404, message="Page not found."), 404

    @app.errorhandler(500)
    def server_error(error):
        return (
            render_template(
                "error.html",
                code=500,
                message="Something went wrong. Please try again later.",
            ),
            500,
        )


def initialize_vercel_fallback_db(app):
    if not app.config.get("VERCEL_SQLITE_FALLBACK"):
        return

    with app.app_context():
        from models import User

        db.create_all()
        admin_email = app.config.get("ADMIN_EMAIL")
        admin_hash = app.config.get("ADMIN_PASSWORD_HASH")
        if admin_email and admin_hash and not User.query.filter_by(email=admin_email).first():
            db.session.add(
                User(
                    full_name="KIRAYA-HAA Admin",
                    email=admin_email,
                    password_hash=admin_hash,
                    role="admin",
                )
            )
            db.session.commit()
        app.logger.warning(
            "Using temporary Vercel SQLite fallback. Set PROD_DATABASE_URL for persistent data."
        )


if __name__ == "__main__":
    create_app().run()
