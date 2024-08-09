from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, PasswordField, SelectField
from wtforms.validators import DataRequired, URL


# WTForm for creating a blog post
class CreateCafeForm(FlaskForm):
    name = StringField("Cafe Name", validators=[DataRequired()])
    map_url = StringField("Google Map Url", validators=[DataRequired(), URL()])
    img_url = StringField("Cafe Image URL", validators=[DataRequired(), URL()])
    location = StringField("City", validators=[DataRequired()])
    has_sockets = SelectField("Has Sockets", choices=["Yes", "No"],
                                validators=[DataRequired()])
    has_wifi = SelectField("Has Wifi", choices=["Yes", "No"],
                              validators=[DataRequired()])
    has_toilet = SelectField("Has Toilet", choices=["Yes", "No"],
                           validators=[DataRequired()])
    can_take_calls = SelectField("Can take calls", choices=["Yes", "No"],
                             validators=[DataRequired()])
    seats = SelectField("Number of Seats", choices=["0-10", "10-20", '20-30', '30-40', '40-50', '50+'],
                                 validators=[DataRequired()])
    coffee_price = StringField("Avg. Coffee Price. Example: 2.7",validators=[DataRequired()])
    submit = SubmitField("Submit")


# TODO: Create a RegisterForm to register new users
class RegisterForm(FlaskForm):
    email = EmailField('Email', validators= [DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField("Register")



# TODO: Create a LoginForm to login existing users
class LoginForm(FlaskForm):
    email = EmailField('Email', validators= [DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField("Log in")


