from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import Enum

from extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(
        Enum("owner", "renter", "admin", name="user_role"),
        nullable=False,
        default="renter",
    )
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    listings = db.relationship(
        "Listing",
        back_populates="owner",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    inquiries = db.relationship(
        "Inquiry",
        back_populates="renter",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def get_id(self):
        return str(self.user_id)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Listing(db.Model):
    __tablename__ = "listings"

    listing_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    title = db.Column(db.String(200), nullable=False)
    property_type = db.Column(
        Enum("flat", "room", "house", "shop", name="property_type"),
        nullable=False,
    )
    area = db.Column(db.String(100), nullable=False)
    rent_pkr = db.Column(db.Integer, nullable=False)
    num_rooms = db.Column(db.SmallInteger, nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(
        Enum("pending", "approved", "rejected", "rented", name="listing_status"),
        nullable=False,
        default="pending",
    )
    rejection_reason = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    owner = db.relationship("User", back_populates="listings")
    photos = db.relationship(
        "Photo",
        back_populates="listing",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    inquiries = db.relationship(
        "Inquiry",
        back_populates="listing",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def primary_photo(self):
        if not self.photos:
            return None
        primary = next((photo for photo in self.photos if photo.is_primary), None)
        return primary or self.photos[0]


class Photo(db.Model):
    __tablename__ = "photos"

    photo_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    listing_id = db.Column(
        db.Integer,
        db.ForeignKey("listings.listing_id", ondelete="CASCADE"),
        nullable=False,
    )
    filename = db.Column(db.String(255), nullable=False, unique=True)
    is_primary = db.Column(db.Boolean, nullable=False, default=False)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    listing = db.relationship("Listing", back_populates="photos")


class Inquiry(db.Model):
    __tablename__ = "inquiries"

    inquiry_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    listing_id = db.Column(
        db.Integer,
        db.ForeignKey("listings.listing_id", ondelete="CASCADE"),
        nullable=False,
    )
    renter_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    phone_number = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(
        Enum("new", "responded", "closed", name="inquiry_status"),
        nullable=False,
        default="new",
    )
    submitted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    listing = db.relationship("Listing", back_populates="inquiries")
    renter = db.relationship("User", back_populates="inquiries")


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    token_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash = db.Column(db.String(255), nullable=False, unique=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship("User")
