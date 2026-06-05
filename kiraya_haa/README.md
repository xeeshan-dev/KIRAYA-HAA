# KIRAYA-HAA

KIRAYA-HAA is a Flask-based property rental listing portal for Gilgit City, Pakistan. It supports owner/renter accounts, moderated property listings, search and filtering, renter inquiries, and a single admin panel.

## Tech Stack

- Python 3.10+
- Flask 2.x
- Flask-SQLAlchemy
- Flask-Login
- Flask-Bcrypt
- Flask-WTF
- Flask-Mail
- SQLite for development
- MySQL for production
- Tailwind CSS via CDN

## Setup

1. Create and activate a virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
pip install -r requirements.txt
```

3. Create `.env` from `.env.example` and fill in real values.

Required environment variables:

- `SECRET_KEY`
- `FLASK_ENV`
- `DEV_DATABASE_URL`
- `PROD_DATABASE_URL`
- `MAIL_SERVER`
- `MAIL_PORT`
- `MAIL_USE_TLS`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`
- `MAIL_DEFAULT_SENDER`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD_HASH`
- `UPLOAD_FOLDER`
- `MAX_CONTENT_LENGTH`

4. Generate an admin password hash.

```powershell
python -c "from flask_bcrypt import Bcrypt; b=Bcrypt(); print(b.generate_password_hash('your-admin-password', rounds=12).decode())"
```

Place the output in `ADMIN_PASSWORD_HASH`.

5. Initialize the database.

```powershell
python migrations/init_db.py
```

6. Run the app locally.

```powershell
flask --app app:create_app run
```

Open `http://127.0.0.1:5000`.

## User Flows

- Guests can browse approved listings.
- Owners can register, log in, create listings, upload up to five JPEG/PNG photos, edit/delete their own listings, and view inquiries.
- Renters can register, log in, browse listings, and submit one inquiry per listing per 24 hours.
- Admins can log in at `/admin/login`, approve/reject/delete listings, suspend/delete users, and view dashboard statistics.

## Deployment Notes

- Set `FLASK_ENV=production`.
- Set `PROD_DATABASE_URL` to a MySQL connection string.
- Store every secret in Render/Railway environment variables.
- Run `python migrations/init_db.py` once during deployment setup.
- Uploaded photos are stored under `static/uploads` for v1.0.

## Out of Scope

KIRAYA-HAA v1.0 does not include payments, real-time chat, maps/geolocation, lease generation, native mobile apps, multi-admin roles, CDN storage, saved searches, listing analytics, task queues, or a separate JSON API.
