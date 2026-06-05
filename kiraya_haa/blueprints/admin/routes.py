from datetime import datetime, timedelta

from flask import abort, current_app, flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user
from flask_mail import Message

from blueprints.admin import admin_bp
from blueprints.admin.forms import AdminLoginForm, RejectListingForm
from blueprints.listings.routes import delete_listing_files
from extensions import bcrypt, db, mail
from models import Inquiry, Listing, User


def admin_required():
    if not current_user.is_authenticated or current_user.role != "admin":
        abort(403)


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated and current_user.role == "admin":
        return redirect(url_for("admin.dashboard"))

    form = AdminLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower(), role="admin").first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            if not user.is_active:
                flash("Your account has been suspended. Contact the administrator.", "error")
            else:
                login_user(user)
                return redirect(url_for("admin.dashboard"))
        else:
            flash("Invalid email or password", "error")
    return render_template("admin/login.html", form=form)


@admin_bp.route("/")
@login_required
def dashboard():
    admin_required()
    since = datetime.utcnow() - timedelta(days=30)
    stats = {
        "users": User.query.count(),
        "pending": Listing.query.filter_by(status="pending").count(),
        "approved": Listing.query.filter_by(status="approved").count(),
        "rejected": Listing.query.filter_by(status="rejected").count(),
        "rented": Listing.query.filter_by(status="rented").count(),
        "recent_inquiries": Inquiry.query.filter(Inquiry.submitted_at >= since).count(),
    }
    return render_template("admin/dashboard.html", stats=stats)


@admin_bp.route("/listings")
@login_required
def listings():
    admin_required()
    all_listings = Listing.query.order_by(Listing.created_at.desc()).all()
    reject_form = RejectListingForm()
    return render_template(
        "admin/listings.html",
        listings=all_listings,
        reject_form=reject_form,
    )


@admin_bp.route("/listings/<int:listing_id>/approve", methods=["POST"])
@login_required
def approve_listing(listing_id):
    admin_required()
    listing = Listing.query.get_or_404(listing_id)
    listing.status = "approved"
    listing.rejection_reason = None
    db.session.commit()
    flash("Listing approved.", "success")
    return redirect(url_for("admin.listings"))


@admin_bp.route("/listings/<int:listing_id>/reject", methods=["POST"])
@login_required
def reject_listing(listing_id):
    admin_required()
    listing = Listing.query.get_or_404(listing_id)
    form = RejectListingForm()
    if form.validate_on_submit():
        listing.status = "rejected"
        listing.rejection_reason = form.reason.data.strip()
        db.session.commit()
        send_rejection_email(listing)
        flash("Listing rejected.", "success")
    else:
        flash("A rejection reason is required.", "error")
    return redirect(url_for("admin.listings"))


@admin_bp.route("/listings/<int:listing_id>/delete", methods=["POST"])
@login_required
def delete_listing(listing_id):
    admin_required()
    listing = Listing.query.get_or_404(listing_id)
    delete_listing_files(listing)
    db.session.delete(listing)
    db.session.commit()
    flash("Listing deleted.", "success")
    return redirect(url_for("admin.listings"))


@admin_bp.route("/users")
@login_required
def users():
    admin_required()
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/users/<int:user_id>/suspend", methods=["POST"])
@login_required
def suspend_user(user_id):
    admin_required()
    user = User.query.get_or_404(user_id)
    if user.role == "admin":
        flash("Admin account cannot be suspended here.", "error")
    else:
        user.is_active = not user.is_active
        db.session.commit()
        flash("User status updated.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
def delete_user(user_id):
    admin_required()
    user = User.query.get_or_404(user_id)
    if user.role == "admin":
        flash("Admin account cannot be deleted here.", "error")
        return redirect(url_for("admin.users"))

    for listing in list(user.listings):
        delete_listing_files(listing)
    db.session.delete(user)
    db.session.commit()
    flash("User and associated data deleted.", "success")
    return redirect(url_for("admin.users"))


def send_rejection_email(listing):
    try:
        mail.send(
            Message(
                "KIRAYA-HAA listing rejected",
                recipients=[listing.owner.email],
                body=(
                    f"Your listing '{listing.title}' was rejected.\n\n"
                    f"Reason: {listing.rejection_reason}"
                ),
            )
        )
    except Exception as exc:
        current_app.logger.warning("Listing rejection email failed: %s", exc)
