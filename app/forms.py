from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, DateField, IntegerField, SelectField, FormField, FileField
from wtforms.validators import DataRequired, Length, EqualTo, NumberRange, ValidationError
from wtforms_alchemy import QuerySelectMultipleField
from wtforms import widgets
from re import search, compile


class UserCheck:
    """Class to check for banned characters / words"""
    # Get arguments that are given when first called
    def __init__(self, banned, regex, message=None):
        self.banned = banned
        self.regex = regex
        self.message = message

    # Activates after initialisation
    def __call__(self, form, field):
        # Turns argument bad characters into regex object
        p = compile(self.regex)
        # Sets user input to lowercase and banned words to lowercase
        if field.data.lower() in (word.lower() for word in self.banned):
            # If user input contains banned word, raise ValidationError
            raise ValidationError(self.message)
        # If regex finds a banned character, raise ValidationError
        if search(p, field.data.lower()):
            raise ValidationError(self.message)


# WTForm data
class ProfileForm(FlaskForm):
    """WTForm for profile pictures (pfp)"""
    img_file = FileField("Choose file")
    about_me = StringField("About me", validators=[Length(min=1, max=150, message="Must be within 1-150 characters")])
    discord_name = StringField("Discord Username", valdiators=[Length(min=2, max=32, message="Must be within 2-37 characters as per discord username rules")])
    discord_id = IntegerField("Discord ID", validators=[NumberRange(min=4, max=4, message="Username ID requires 4 numbers")])
    submit = SubmitField("Upload file")


class FollowForm(FlaskForm):
    """Checks if user has followed"""
    submit = SubmitField()


class LoginForm(FlaskForm):
    """WTForm for login.html"""
    username = StringField("Username", validators=[DataRequired(), Length(min=1, max=20, message="Must be within 1-20 characters"), UserCheck(message="Special characters not allowed",
                  banned=['root', 'admin', 'sys', 'administrator'],
                  regex="^(?=.*[-+_!@#$%^&*., ?]) ")])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=1, max=20, message="Must be within 1-20 characters"), UserCheck(message="Special characters not allowed",
                  banned=['root', 'admin', 'sys', 'administrator'],
                  regex="^(?=.*[-+_!@#$%^&*., ?]) ")])
    submit = SubmitField("Submit")


class SignForm(FlaskForm):
    """WTForm for signup.html"""
    username = StringField("Username", validators=[DataRequired(), Length(min=1, max=20, message="Must be within 1-20 characters"), UserCheck(message="Special characters not allowed",
                  banned=['root', 'admin', 'sys', 'administrator'],
                  regex="^(?=.*[-+_!@#$%^&*., ?]) ")])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=20, message="Must be within 6-20 characters"), EqualTo('confirm', message="Both password and reconfirm password must be the same"), UserCheck(message="Special characters not allowed",
                  banned=['root', 'admin', 'sys', 'administrator'],
                  regex="^(?=.*[-+_!@#$%^&*., ?]) ")])
    confirm = PasswordField("Reconfirm password", validators=[DataRequired(), Length(min=6, max=20,)])
    dob = DateField('D.O.B', validators=[DataRequired()])
    submit = SubmitField("Change page")


class CheckboxMultiField(QuerySelectMultipleField):
    """Manages the widget for the Checkbox widget. To be combined with CombinedForm."""
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class PageForm(FlaskForm):
    """WTForm for page change in search.html"""
    page_num = IntegerField("Page", validators=[NumberRange(min=1, message="Page number goes above or below limit!"), DataRequired()])
    submit = SubmitField("Submit")


class GenCatForm(FlaskForm):
    """WTForm for managing genre / category choices"""
    genres = CheckboxMultiField("Genres")
    categories = CheckboxMultiField("Categories")


class SortForm(FlaskForm):
    """WTForm for managing sort styles and ASC and DESC and user input"""
    search_query = StringField("Search: ", validators=[Length(max=30)])
    sort_style = SelectField("Sort Style", validators=[DataRequired()])
    sort_asc = SelectField("Sort ASC/DESC", validators=[DataRequired()])


class CombinedForm(FlaskForm):
    """Manages sort_styles, ASC DESC, user_input, gen/cat choices"""
    gen_form = FormField(GenCatForm)
    sort_form = FormField(SortForm)
    submit = SubmitField("Submit")
