from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from blueprints.inquiries.forms import InquiryForm
from blueprints.listings import listings_bp
from blueprints.listings.forms import ListingForm, SearchForm
from blueprints.listings.utils import delete_photo, save_photo
from extensions import db
from models import Listing, Photo


def owner_required():
    if not current_user.is_authenticated:
        return False
    return current_user.role == "owner"


def apply_listing_form(listing, form):
    listing.title = form.title.data.strip()
    listing.property_type = form.property_type.data
    listing.area = form.area.data
    listing.rent_pkr = form.rent_pkr.data
    listing.num_rooms = form.num_rooms.data
    listing.description = form.description.data.strip()


def delete_listing_files(listing):
    for photo in list(listing.photos):
        delete_photo(photo.filename)


@listings_bp.route("/")
def browse():
    form = SearchForm(request.args, meta={"csrf": False})
    include_rented = request.args.get("include_rented") == "1"
    page = request.args.get("page", 1, type=int)

    query = Listing.query
    if include_rented:
        query = query.filter(Listing.status.in_(["approved", "rented"]))
    else:
        query = query.filter_by(status="approved")

    if form.q.data:
        term = f"%{form.q.data.strip()}%"
        query = query.filter(or_(Listing.title.ilike(term), Listing.description.ilike(term)))
    if form.area.data:
        query = query.filter_by(area=form.area.data)
    if form.property_type.data:
        query = query.filter_by(property_type=form.property_type.data)
    if form.min_price.data is not None:
        query = query.filter(Listing.rent_pkr >= form.min_price.data)
    if form.max_price.data is not None:
        query = query.filter(Listing.rent_pkr <= form.max_price.data)
    if form.min_rooms.data is not None:
        query = query.filter(Listing.num_rooms >= form.min_rooms.data)

    if form.sort.data == "price_asc":
        query = query.order_by(Listing.rent_pkr.asc())
    elif form.sort.data == "price_desc":
        query = query.order_by(Listing.rent_pkr.desc())
    else:
        query = query.order_by(Listing.created_at.desc())

    pagination = query.paginate(page=page, per_page=12, error_out=False)
    query_args = request.args.to_dict(flat=True)
    query_args.pop("page", None)
    return render_template(
        "listings/browse.html",
        form=form,
        listings=pagination.items,
        pagination=pagination,
        include_rented=include_rented,
        query_args=query_args,
    )


@listings_bp.route("/<int:listing_id>")
def detail(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    can_view_private = (
        current_user.is_authenticated
        and (
            current_user.role == "admin"
            or (
                current_user.role == "owner"
                and listing.owner_id == current_user.user_id
            )
        )
    )
    if not can_view_private and listing.status != "approved":
        abort(404)
    inquiry_form = InquiryForm() if current_user.is_authenticated else None
    return render_template(
        "listings/detail.html",
        listing=listing,
        inquiry_form=inquiry_form,
    )


@listings_bp.route("/dashboard")
@login_required
def dashboard():
    if not owner_required():
        abort(403)
    listings = (
        Listing.query.filter_by(owner_id=current_user.user_id)
        .order_by(Listing.created_at.desc())
        .all()
    )
    return render_template("listings/dashboard.html", listings=listings)


@listings_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_listing():
    if not owner_required():
        abort(403)
    form = ListingForm()
    if form.validate_on_submit():
        listing = Listing(owner_id=current_user.user_id, status="pending")
        apply_listing_form(listing, form)
        db.session.add(listing)
        db.session.flush()

        try:
            add_uploaded_photos(listing, form)
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "error")
            return render_template("listings/add_listing.html", form=form)

        db.session.commit()
        flash("Listing submitted for admin approval.", "success")
        return redirect(url_for("listings.dashboard"))
    return render_template("listings/add_listing.html", form=form)


@listings_bp.route("/<int:listing_id>/edit", methods=["GET", "POST"])
@login_required
def edit_listing(listing_id):
    if not owner_required():
        abort(403)
    listing = Listing.query.get_or_404(listing_id)
    if listing.owner_id != current_user.user_id:
        abort(403)

    form = ListingForm(obj=listing)
    if form.validate_on_submit():
        apply_listing_form(listing, form)
        listing.status = "pending"
        listing.rejection_reason = None
        try:
            add_uploaded_photos(listing, form)
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template("listings/edit_listing.html", form=form, listing=listing)
        db.session.commit()
        flash("Listing updated and sent for re-approval.", "success")
        return redirect(url_for("listings.dashboard"))
    return render_template("listings/edit_listing.html", form=form, listing=listing)


@listings_bp.route("/<int:listing_id>/delete", methods=["POST"])
@login_required
def delete_listing(listing_id):
    if not owner_required():
        abort(403)
    listing = Listing.query.get_or_404(listing_id)
    if listing.owner_id != current_user.user_id:
        abort(403)
    delete_listing_files(listing)
    db.session.delete(listing)
    db.session.commit()
    flash("Listing deleted.", "success")
    return redirect(url_for("listings.dashboard"))


@listings_bp.route("/<int:listing_id>/toggle", methods=["POST"])
@login_required
def toggle_listing(listing_id):
    if not owner_required():
        abort(403)
    listing = Listing.query.get_or_404(listing_id)
    if listing.owner_id != current_user.user_id:
        abort(403)
    if listing.status == "rented":
        listing.status = "approved"
    elif listing.status == "approved":
        listing.status = "rented"
    else:
        flash("Only approved listings can be toggled available or rented.", "error")
        return redirect(url_for("listings.dashboard"))
    db.session.commit()
    flash("Listing availability updated.", "success")
    return redirect(url_for("listings.dashboard"))


def add_uploaded_photos(listing, form):
    files = [file for file in form.photos.data or [] if file and file.filename]
    if len(listing.photos) + len(files) > 5:
        raise ValueError("A listing can have up to 5 photos.")

    for file_storage in files:
        filename = save_photo(file_storage, listing.listing_id)
        photo = Photo(
            listing_id=listing.listing_id,
            filename=filename,
            is_primary=len(listing.photos) == 0,
        )
        db.session.add(photo)
