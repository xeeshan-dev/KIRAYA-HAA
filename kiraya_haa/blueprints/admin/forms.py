from flask_wtf import FlaskForm
from wtforms import EmailField, HiddenField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length


class AdminLoginForm(FlaskForm):
    email = EmailField("Admin email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Admin login")


class RejectListingForm(FlaskForm):
    reason = StringField("Rejection reason", validators=[DataRequired(), Length(max=500)])
    submit = SubmitField("Reject listing")


class IdForm(FlaskForm):
    item_id = HiddenField("Item ID", validators=[DataRequired()])
    submit = SubmitField("Confirm")
