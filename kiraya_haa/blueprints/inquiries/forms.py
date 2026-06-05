from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Regexp


class InquiryForm(FlaskForm):
    phone_number = StringField(
        "Phone number",
        validators=[
            DataRequired(),
            Length(max=20),
            Regexp(r"^[0-9+\-\s()]+$", message="Enter a valid phone number."),
        ],
    )
    message = TextAreaField("Message", validators=[DataRequired(), Length(max=2000)])
    submit = SubmitField("Send inquiry")


class InquiryStatusForm(FlaskForm):
    status = SelectField(
        "Status",
        choices=[("new", "New"), ("responded", "Responded"), ("closed", "Closed")],
        validators=[DataRequired()],
    )
    submit = SubmitField("Update")
