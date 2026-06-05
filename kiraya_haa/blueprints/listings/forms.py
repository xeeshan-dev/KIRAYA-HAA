from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, MultipleFileField
from wtforms import IntegerField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from constants import GILGIT_AREAS, PROPERTY_TYPES


class ListingForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    property_type = SelectField(
        "Property type",
        choices=[(item, item.title()) for item in PROPERTY_TYPES],
        validators=[DataRequired()],
    )
    area = SelectField(
        "Area",
        choices=[(area, area) for area in GILGIT_AREAS],
        validators=[DataRequired()],
    )
    rent_pkr = IntegerField(
        "Rent per month (PKR)",
        validators=[DataRequired(), NumberRange(min=1)],
    )
    num_rooms = IntegerField(
        "Number of rooms",
        validators=[DataRequired(), NumberRange(min=1, max=50)],
    )
    description = TextAreaField("Description", validators=[DataRequired()])
    photos = MultipleFileField(
        "Photos",
        validators=[Optional(), FileAllowed(["jpg", "jpeg", "png"], "JPEG or PNG only.")],
    )
    submit = SubmitField("Save listing")


class SearchForm(FlaskForm):
    q = StringField("Search", validators=[Optional()])
    area = SelectField(
        "Area",
        choices=[("", "Any area")] + [(area, area) for area in GILGIT_AREAS],
        validators=[Optional()],
    )
    property_type = SelectField(
        "Property type",
        choices=[("", "Any type")] + [(item, item.title()) for item in PROPERTY_TYPES],
        validators=[Optional()],
    )
    min_price = IntegerField("Min price", validators=[Optional(), NumberRange(min=0)])
    max_price = IntegerField("Max price", validators=[Optional(), NumberRange(min=0)])
    min_rooms = IntegerField("Min rooms", validators=[Optional(), NumberRange(min=1)])
    sort = SelectField(
        "Sort",
        choices=[
            ("newest", "Newest First"),
            ("price_asc", "Price: Low to High"),
            ("price_desc", "Price: High to Low"),
        ],
        default="newest",
    )
