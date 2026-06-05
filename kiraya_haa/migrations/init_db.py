import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app  # noqa: E402
from extensions import db  # noqa: E402
from models import User  # noqa: E402


def seed_admin(app):
    admin_email = app.config.get("ADMIN_EMAIL")
    admin_hash = app.config.get("ADMIN_PASSWORD_HASH")
    if not admin_email or not admin_hash:
        app.logger.warning("ADMIN_EMAIL or ADMIN_PASSWORD_HASH missing; admin not seeded.")
        return

    admin = User.query.filter_by(email=admin_email).first()
    if admin:
        admin.full_name = "KIRAYA-HAA Admin"
        admin.password_hash = admin_hash
        admin.role = "admin"
        admin.is_active = True
    else:
        admin = User(
            full_name="KIRAYA-HAA Admin",
            email=admin_email,
            password_hash=admin_hash,
            role="admin",
        )
        db.session.add(admin)
    db.session.commit()


def main():
    os.environ.setdefault("FLASK_ENV", "development")
    app = create_app()
    with app.app_context():
        db.create_all()
        seed_admin(app)
        print("Database initialized.")


if __name__ == "__main__":
    main()
