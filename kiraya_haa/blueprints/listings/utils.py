import imghdr
import os
import uuid
from pathlib import Path

from flask import current_app, url_for
from werkzeug.utils import secure_filename


def _upload_dir():
    return Path(current_app.root_path) / current_app.config["UPLOAD_FOLDER"]


def _extension(filename):
    return filename.rsplit(".", 1)[1].lower() if "." in filename else ""


def save_photo(file_storage, listing_id) -> str:
    """
    Validates, saves, and returns the UUID-based filename.
    Raises ValueError if file type is invalid.
    Raises IOError if save fails.
    """
    if not file_storage or not file_storage.filename:
        raise ValueError("No file selected.")

    ext = _extension(secure_filename(file_storage.filename))
    if ext not in current_app.config["ALLOWED_EXTENSIONS"]:
        raise ValueError("Only JPEG and PNG photos are allowed.")
    if file_storage.mimetype not in {"image/jpeg", "image/png"}:
        raise ValueError("Only JPEG and PNG photos are allowed.")

    file_storage.stream.seek(0, os.SEEK_END)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size > 5 * 1024 * 1024:
        raise ValueError("Each photo must be 5 MB or smaller.")

    header = file_storage.stream.read(512)
    file_storage.stream.seek(0)
    detected = imghdr.what(None, header)
    if detected == "jpeg":
        detected = "jpg"
    if detected not in {"jpg", "png"}:
        raise ValueError("Only JPEG and PNG photos are allowed.")

    filename = f"{listing_id}_{uuid.uuid4().hex}.{ext}"
    path = _upload_dir() / filename
    try:
        file_storage.save(path)
    except OSError as exc:
        raise IOError("Could not save photo.") from exc
    return filename


def delete_photo(filename) -> None:
    """
    Deletes the file from the upload folder.
    Silently ignores if file does not exist.
    """
    if not filename:
        return
    try:
        os.remove(_upload_dir() / filename)
    except FileNotFoundError:
        return


def get_photo_url(filename) -> str:
    """
    Returns the URL path to serve the photo.
    This abstraction allows future migration to CDN by changing only this function.
    """
    if not filename:
        return url_for("static", filename="img/placeholder-property.svg")
    return url_for("static", filename=f"uploads/{filename}")
