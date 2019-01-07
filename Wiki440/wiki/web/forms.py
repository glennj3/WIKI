"""
    Forms
    ~~~~~
"""
from flask_wtf import Form, FlaskForm
from wtforms import BooleanField
from wtforms import TextField
from wtforms import TextAreaField
from wtforms import PasswordField
from wtforms import StringField
from wtforms.validators import Length
from wtforms.validators import EqualTo
from wtforms.validators import InputRequired
from wtforms.validators import ValidationError

from wiki.core import clean_url
from wiki.web import current_wiki
from wiki.web import current_users
from wiki.web import UserManager


class URLForm(Form):
    url = TextField('', [InputRequired()])

    def validate_url(form, field):
        if current_wiki.exists(field.data):
            raise ValidationError('The URL "%s" exists already.' % field.data)

    def clean_url(self, url):
        return clean_url(url)


class SearchForm(Form):
    term = TextField('', [InputRequired()])
    ignore_case = BooleanField(
        description='Ignore Case',
        # FIXME: default is not correctly populated
        default=True)


class EditorForm(Form):
    title = TextField('', [InputRequired()])
    body = TextAreaField('', [InputRequired()])
    tags = TextField('')


class LoginForm(Form):
    name = TextField('', [InputRequired()])
    password = PasswordField('', [InputRequired()])

    def validate_name(form, field):
        user = current_users.get_user(field.data)
        if not user:
            raise ValidationError('This username does not exist.')

    def validate_password(form, field):
        user = current_users.get_user(form.name.data)
        if not user:
            return
        if not user.check_password(field.data):
            raise ValidationError('Username and password do not match.')

"""
Register Form allows the user to submit a new username and password combination as long as the validators are passed.
"""
class RegisterForm(Form):
    username = StringField('Username', [InputRequired('Must have input'), Length(min=4, message='Length must be greater than 4.')])
    password = PasswordField('New Password', [InputRequired(), EqualTo('confirm', message='Passwords Must Match'), Length(min=4, max=25, message='Length must be greater than 3.')])
    confirm = PasswordField('Repeat Password')

    def validate_name(form, field):
        valid = UserManager(current_users).get_user(form.username.data)
        if valid:
            raise ValidationError("Username Invalid")
        elif valid is None:
            return

    def validate_password(form, field):
        # password = form.password.data
        return
"""
Profile edit form is for submitting values to be changed in an individual users profile.
"""
class profileeditForm(Form):
    location = StringField('Location')
    bio = StringField('Bio')
    gender = StringField('Gender')
    speciality = StringField('Speciality')
    picture = StringField('Picture Name')

    def validate_something(form, field):
        return