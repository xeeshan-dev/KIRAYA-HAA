import hashlib
import secrets
from datetime import datetime, timedelta

from flask import current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from flask_mail import Message

from blueprints.auth import auth_bp
from blueprints.auth.forms import ForgotPasswordForm, LoginForm, RegisterForm, ResetPasswordForm
from extensions import bcrypt, db, mail
from models import PasswordResetToken, User


def hash_token(raw_token):
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.query.filter_by(email=email).first():
            form.email.errors.append("This email is already registered.")
        else:
            user = User(
                full_name=form.full_name.data.strip(),
                email=email,
                password_hash=bcrypt.generate_password_hash(
                    form.password.data, rounds=12
                ).decode("utf-8"),
                role=form.role.data,
            )
            db.session.add(user)
            db.session.commit()
            flash("Account created. Please log in.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            if not user.is_active:
                flash("Your account has been suspended. Contact the administrator.", "error")
                return render_template("auth/login.html", form=form)
            login_user(user)
            return redirect(request.args.get("next") or url_for("index"))
        flash("Invalid email or password", "error")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and user.role != "admin":
            raw_token = secrets.token_urlsafe(32)
            reset_token = PasswordResetToken(
                user_id=user.user_id,
                token_hash=hash_token(raw_token),
                expires_at=datetime.utcnow() + timedelta(minutes=60),
            )
            db.session.add(reset_token)
            db.session.commit()
            reset_url = url_for("auth.reset_password", token=raw_token, _external=True)
            try:
                mail.send(
                    Message(
                        "KIRAYA-HAA password reset",
                        recipients=[user.email],
                        body=(
                            "Use this link to reset your password. "
                            f"It expires in 60 minutes:\n{reset_url}"
                        ),
                    )
                )
            except Exception as exc:
                current_app.logger.warning("Password reset email failed: %s", exc)
        flash("If that email exists, a reset link has been sent.", "info")
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot_password.html", form=form)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    token_hash = hash_token(token)
    reset_token = PasswordResetToken.query.filter_by(token_hash=token_hash).first()
    session_token_id = session.get("reset_token_id")
    invalid = (
        not reset_token
        or (reset_token.is_used and session_token_id != reset_token.token_id)
        or reset_token.expires_at < datetime.utcnow()
    )
    if invalid:
        flash("This link has expired or already been used", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "GET" and not reset_token.is_used:
        reset_token.is_used = True
        session["reset_token_id"] = reset_token.token_id
        db.session.commit()

    form = ResetPasswordForm()
    if form.validate_on_submit():
        reset_token.user.password_hash = bcrypt.generate_password_hash(
            form.password.data, rounds=12
        ).decode("utf-8")
        session.pop("reset_token_id", None)
        db.session.commit()
        flash("Password reset complete. Please log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/reset_password.html", form=form)
