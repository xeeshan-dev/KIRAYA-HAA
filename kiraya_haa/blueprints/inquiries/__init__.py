from flask import Blueprint

inquiries_bp = Blueprint("inquiries", __name__, url_prefix="/inquiries")

from blueprints.inquiries import routes  # noqa: E402,F401
