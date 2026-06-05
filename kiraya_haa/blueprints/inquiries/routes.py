from datetime import datetime, timedelta

from flask import abort, current_app, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from flask_mail import Message

from blueprints.inquiries import inquiries_bp
from blueprints.inquiries.forms import InquiryForm, InquiryStatusForm
from extensions import db, mail
from models import Inquiry, Listing


def renter_required():
    return current_user.is_authenticated and current_user.role == "renter"


def owner_required():
    return current_user.is_authenticated and current_user.role == "owner"


@inquiries_bp.route("/listing/<int:listing_id>/submit", methods=["POST"])
@login_required
def submit(listing_id):
    if not renter_required():
        abort(403)

    listing = Listing.query.get_or_404(listing_id)
    if listing.status != "approved":
        abort(403)

    form = InquiryForm()
    if form.validate_on_submit():
        cutoff = datetime.utcnow() - timedelta(hours=24)
        duplicate = Inquiry.query.filter(
            Inquiry.renter_id == current_user.user_id,
            Inquiry.listing_id == listing.listing_id,
            Inquiry.submitted_at >= cutoff,
        ).first()
        if duplicate:
            flash("You already sent an inquiry for this listing in the last 24 hours.", "error")
            return redirect(url_for("listings.detail", listing_id=listing.listing_id))

        inquiry = Inquiry(
            listing_id=listing.listing_id,
            renter_id=current_user.user_id,
            phone_number=form.phone_number.data.strip(),
            message=form.message.data.strip(),
        )
        db.session.add(inquiry)
        db.session.commit()
        send_inquiry_email(listing, inquiry)
        flash("Inquiry sent to the owner.", "success")
    else:
        flash("Please check the inquiry form fields.", "error")
    return redirect(url_for("listings.detail", listing_id=listing.listing_id))


@inquiries_bp.route("/inbox")
@login_required
def inbox():
    if not owner_required():
        abort(403)
    inquiries = (
        Inquiry.query.join(Listing)
        .filter(Listing.owner_id == current_user.user_id)
        .order_by(Inquiry.submitted_at.desc())
        .all()
    )
    status_form = InquiryStatusForm()
    return render_template(
        "inquiries/inbox.html",
        inquiries=inquiries,
        status_form=status_form,
    )


@inquiries_bp.route("/<int:inquiry_id>/status", methods=["POST"])
@login_required
def update_status(inquiry_id):
    if not owner_required():
        abort(403)
    inquiry = Inquiry.query.get_or_404(inquiry_id)
    if inquiry.listing.owner_id != current_user.user_id:
        abort(403)
    form = InquiryStatusForm()
    if form.validate_on_submit():
        inquiry.status = form.status.data
        db.session.commit()
        flash("Inquiry status updated.", "success")
    else:
        flash("Invalid inquiry status.", "error")
    return redirect(url_for("inquiries.inbox"))


def send_inquiry_email(listing, inquiry):
    try:
        mail.send(
            Message(
                "New KIRAYA-HAA inquiry",
                recipients=[listing.owner.email],
                body=(
                    f"Listing: {listing.title}\n"
                    f"Renter: {inquiry.renter.full_name}\n"
                    f"Phone: {inquiry.phone_number}\n\n"
                    f"{inquiry.message}\n\n"
                    f"View listing: {url_for('listings.detail', listing_id=listing.listing_id, _external=True)}"
                ),
            )
        )
    except Exception as exc:
        current_app.logger.warning("Inquiry email failed: %s", exc)
