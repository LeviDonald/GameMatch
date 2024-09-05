'''Game Match Website'''
import sqlite3
from math import ceil
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import Flask, render_template, abort, url_for, request, redirect, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, DateField, IntegerField, SelectField, FormField, FileField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, NumberRange, regexp
from wtforms_alchemy import QuerySelectMultipleField
from wtforms import widgets

app = Flask(__name__)

DATABASE = "gamematch.db"
HOME = "home.html"
GAMES = "games.html"
SEARCH_GAMES = "search.html"
SELECTED_GAME = "selected_game.html"
LOGIN = "login.html"
LOGOUT = "logout.html"
SIGNUP = "signup.html"
FAV_GAME = "fav_games.html"
FAV_IMAGE = "fav_image.html"
USER_PROFILE = "user_profile.html"
ERROR404 = "404.html"
LIMIT = 5

app.config['SECRET_KEY'] = '1e5ec2a58f909c4edbe7ffb3a7dcd84d'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gamematch.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


@app.before_request
def make_session_permanent():
    session.permanent = True


db = SQLAlchemy(app)

epic_engine = create_engine('sqlite:///gamematch.db')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# Easy query process function (TO DO: possibly convert into class)
# Use when using SELECT queries :)
def select_database(query, id=None):
    """Selects raw queries (SELECT)"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        if id:
            cursor.execute(query, id)
        else:
            cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as exception:
        abort(404, exception)


# Use when using queries which include:
# UPDATE, DROP, DELETE, INSERT and etc.
def commit_database(query, id=None):
    """Commits raw queries (INSERT, DELETE etc.)"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        if id:
            cursor.execute(query, id)
        else:
            cursor.execute(query)
        conn.commit()
        conn.close()
    except Exception as exception:
        abort(404, exception)


def remove_bad_games(ids, name):
    """Deletes bad games based off of keywords"""
    # Goes through each inappropriate ID
    for i in ids:
        # Gets every game ID which is associated with this tag
        bad_games = select_database("SELECT {}_id FROM game_tag WHERE {}_id = ?;".format(name, name), (i,))
        # Removes each bad game from games
        for game in bad_games:
            commit_database("DELETE FROM games WHERE game_id = ?;", (game[0],))
        # Disposes of unnecessary data from bridge table
        commit_database("DELETE FROM game_{} WHERE {}_id = ?".format(name, name), (i,))


def one_id_bugfix(sort_list):
    """Removes the tuple comma at the end to make SQL not break"""
    # If only one item in tuple
    if len(sort_list) == 1:
        # Remove comma
        sort_list = f"({sort_list[0]})"
    # If multiple items, return full list
    return sort_list


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
        p = re.compile(self.regex)
        # Sets user input to lowercase and banned words to lowercase
        if field.data.lower() in (word.lower() for word in self.banned):
            # If user input contains banned word, raise ValidationError
            raise ValidationError(self.message)
        # If regex finds a banned character, raise ValidationError
        if re.search(p, field.data.lower()):
            raise ValidationError(self.message)


# Setting up tables to be used with SQLAlchemy
class Users(db.Model, UserMixin):
    """users SQLAlchemy Table"""
    __tablename__ = "user"
    username = db.Column(db.String, primary_key=True)
    password = db.Column(db.String, nullable=False)

    def get_id(self):
        return self.username


class FavouriteGames(db.Model):
    """favourite_games SQLAlchemy Table"""
    __table__ = db.Table('favourite_games', db.metadata, autoload_with=epic_engine)


class Games(db.Model):
    """games SQLAlchemy Table"""
    __table__ = db.Table('games', db.metadata, autoload_with=epic_engine)


class Categories(db.Model):
    """categories SQLAlchemy Table"""
    __table__ = db.Table('categorys', db.metadata, autoload_with=epic_engine)

    def __str__(self):
        return self.category_name


class Genres(db.Model):
    """genres SQLAlchemy Table"""
    __table__ = db.Table('genres', db.metadata, autoload_with=epic_engine)

    def __str__(self):
        return self.genre_name


class Publishers(db.Model):
    """publishers SQLAlchemy Table"""
    __table__ = db.Table('publishers', db.metadata, autoload_with=epic_engine)


class Developers(db.Model):
    """developers SQLAlchemy Table"""
    __table__ = db.Table('developers', db.metadata, autoload_with=epic_engine)


class GameCat(db.Model):
    """game_category SQLAlchemy Table"""
    __table__ = db.Table('game_category', db.metadata, autoload_with=epic_engine)


class GameGen(db.Model):
    """game_genre SQLAlchemy Table"""
    __table__ = db.Table('game_genre', db.metadata, autoload_with=epic_engine)


class GamePub(db.Model):
    """game_publisher SQLAlchemy Table"""
    __table__ = db.Table('game_publisher', db.metadata, autoload_with=epic_engine)


class GameDev(db.Model):
    """game_developer SQLAlchemy Table"""
    __table__ = db.Table('game_developer', db.metadata, autoload_with=epic_engine)


# WTForm data
class PFPForm(FlaskForm):
    """WTForm for profile pictures (pfp)"""
    img_file = FileField("Choose file", validators[regexp(u'^[^/\\]\.jpg$')])

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
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class PageForm(FlaskForm):
    """WTForm for page change in search.html"""
    page_num = IntegerField("Page", validators=[NumberRange(min=1, message="Page number goes above or below limit!"), DataRequired()])
    submit = SubmitField("Submit")


class GenCatTagForm(FlaskForm):
    """WTForm for managing genre / category / tag choices"""
    genres = CheckboxMultiField("Genres")
    categories = CheckboxMultiField("Categories")


class SortForm(FlaskForm):
    """WTForm for managing sort styles and ASC and DESC and user input"""
    search_query = StringField("Search: ", validators=[Length(max=30)])
    sort_style = SelectField("Sort Style", validators=[DataRequired()])
    sort_asc = SelectField("Sort ASC/DESC", validators=[DataRequired()])


class CombinedForm(FlaskForm):
    """Manages sort_styles, ASC DESC, user_input, gen/cat/tag choices"""
    gen_form = FormField(GenCatTagForm)
    sort_form = FormField(SortForm)
    submit = SubmitField("Submit")


@login_manager.user_loader
def load_user(user_id):
    """When logging in, gets username"""
    return Users.query.get(str(user_id))


@app.errorhandler(404)
def error_404(exception):
    """Error 404 page. If error occurs, redirect here w/ exception"""
    return render_template(ERROR404, exception=exception)


# Home page
@app.route("/")
def home():
    """Home page"""
    try:
        return render_template(HOME)
    except Exception as e:
        abort(404, e)


@app.route("/login", methods=["POST", "GET"])
def login():
    """Login form. Checks if username and password is correct and then logs in using flask-wtf"""
    try:
        form = LoginForm()
        # When form is submitted
        if form.validate_on_submit():
            # Get user information based on input username
            user_info = Users.query.filter_by(username=form.username.data).first()
            if user_info:
                # Using werkzeug security, check hash stored in DB
                if check_password_hash(user_info.password, form.password.data):
                    # Flask-login logs in the user
                    login_user(user_info, remember=True)
                    return redirect(url_for('home'))
                else:
                    flash("Incorrect username / password")
            else:
                flash("Incorrect username / password")
            return redirect(url_for("home"))
        return render_template(LOGIN, form=form)
    except Exception as e:
        abort(404, e)


@app.route("/signup", methods=["POST", "GET"])
def signup():
    """Sign up form. If user has unique username, encrypt password and add to database"""
    try:
        form = SignForm()
        # When form is submitted
        if form.validate_on_submit():
            # Get Date of Birth from form data
            dob = form.dob.data
            # If user is older than 17 years old (as users are given the possibility to chat through sharing discord info, I put an age limit)
            if dob <= (datetime.today() - relativedelta(years=17)).date():
                # If a result from the DB comes back then the username has already been taken
                user_check = Users.query.filter_by(username=form.username.data).first()
                if user_check:
                    flash("This username has already been taken! Please use a different one.")
                else:
                    # Else, set up a new user with the input username and newly generated hash
                    user = Users()
                    user.username = form.username.data
                    user.password = generate_password_hash(form.password.data, salt_length=16)
                    # Commit changes to the database
                    db.session.add(user)
                    db.session.commit()
                    # Flask-login logs in the user
                    login_user(user, remember=True)
                    return redirect(url_for('home'))
            else:
                flash("You must be older than 16 to join this website :'(")
                return redirect(url_for('home'))
        return render_template(SIGNUP, form=form)
    except Exception as e:
        abort(404, e)


@app.route("/logout")
@login_required
def logout():
    """Logs out via. Flask-login and redirects to logout page"""
    try:
        # Flask-login logs out the user
        logout_user()
        return render_template(LOGOUT)
    except Exception as e:
        abort(404, e)

@app.route("/clear_search/<int:fav>")
def clear_search(fav):
    try:
        session['page'] = 1
        session['genres'] = None
        session['categories'] = None
        session['sort_style'] = 'name'
        session['sort_asc'] = 'ASC'
        session['search_query'] = None
        session['max_pages'] = None
        if fav == 1:
            return redirect(url_for('favourite_games'))
        return redirect(url_for('games'))
    except Exception as e:
        abort(404, e)


@app.route("/change_page/<int:page>/<int:fav>")
def change_page(page, fav):
    try:
        # To prevent people from just altering the page in the search bar to a non-existant page
        if page <= session['max_pages'] and page > 0:
            session['page'] = page
            if fav == 1:
                return redirect(url_for('favourite_games'))
            return redirect(url_for('games'))
    except Exception as e:
        abort(404, e)


@app.route("/games", methods=["POST", "GET"])
def games():
    # try:
    offset = (session['page'] - 1) * LIMIT
    page_form = PageForm()
    combined_form = CombinedForm()
    combined_form.gen_form.genres.query = Genres.query.all()
    combined_form.gen_form.categories.query = Categories.query.all()
    page_form.page_num.default = session['page']
    combined_form.sort_form.sort_style.choices = [('name', 'Alphabetically'), ('playtime', 'Popularity')]
    combined_form.sort_form.sort_asc.choices = [('ASC', 'Ascending'), ('DESC', 'Descending')]
    if page_form.validate_on_submit():
        if page_form.page_num.data:
            session['page'] = page_form.page_num.data
            return redirect(url_for('games'))
    if combined_form.is_submitted() and 'combined' in request.form:
        session['search_query'] = None
        session['max_pages'] = None
        if combined_form.sort_form.sort_style.data == "playtime":
            if combined_form.sort_form.sort_asc.data == "ASC":
                combined_form.sort_form.sort_asc.data = "DESC"
            else:
                combined_form.sort_form.sort_asc.data = "ASC"
        # Can't put in function format because of unique column names (e.g genre_id)
        genres = combined_form.gen_form.genres.data
        categories = combined_form.gen_form.categories.data
        if genres or categories:
            new_list = []
            if genres:
                for genre in genres:
                    new_list.append(genre.genre_id)
                session['genres'] = one_id_bugfix(tuple(new_list))
            new_list = []
            if categories:
                for category in categories:
                    new_list.append(category.category_id)
                session['categories'] = one_id_bugfix(tuple(new_list))
        else:
            session['genres'] = None
            session['categories'] = None
        session['sort_style'] = combined_form.sort_form.sort_style.data
        session['sort_asc'] = combined_form.sort_form.sort_asc.data
        search_query = combined_form.sort_form.search_query.data
        if search_query:
            session['search_query'] = f"%{search_query}%"
        session['page'] = 1
        return redirect(url_for('games'))
    # If user is searching using words
    if session['search_query']:
        # If words + genres
        if session['genres'] or session['categories']:
            if session['genres'] and session['categories']:
                sql_query = "SELECT DISTINCT games.game_id, games.name, games.header_image FROM ((games INNER JOIN game_genre ON games.game_id = game_genre.game_id) INNER JOIN game_category ON games.game_id = game_category.game_id) WHERE games.name LIKE ? AND game_genre.genre_id IN %s AND game_category.category_id IN %s ORDER BY %.8s %.4s LIMIT ? OFFSET ?;" % (session['genres'], session['categories'], session['sort_style'], session['sort_asc'])
                count_query = "SELECT COUNT(*) FROM (SELECT DISTINCT games.game_id, games.name, games.header_image FROM ((games INNER JOIN game_genre ON games.game_id = game_genre.game_id) INNER JOIN game_category ON games.game_id = game_category.game_id) WHERE games.name LIKE ? AND game_genre.genre_id IN %s AND game_category.category_id IN %s);" % (session['genres'], session['categories'])
            elif session['genres']:
                sql_query = "SELECT DISTINCT games.game_id, games.name, games.header_image FROM (games INNER JOIN game_genre ON games.game_id = game_genre.game_id) WHERE games.name LIKE ? AND game_genre.genre_id IN %s ORDER BY %.8s %.4s LIMIT ? OFFSET ?;" % (session['genres'], session['sort_style'], session['sort_asc'])
                count_query = "SELECT COUNT(*) FROM (SELECT DISTINCT games.game_id, games.name, games.header_image FROM (games INNER JOIN game_genre ON games.game_id = game_genre.game_id) WHERE games.name LIKE ? AND game_genre.genre_id IN %s)" % (session['genres'],)
            else:
                sql_query = "SELECT DISTINCT games.game_id, games.name, games.header_image FROM (games INNER JOIN game_category ON games.game_id = game_category.game_id) WHERE games.name LIKE ? AND game_category.category_id IN %s ORDER BY %.8s %.4s LIMIT ? OFFSET ?;" % (session['categories'], session['sort_style'], session['sort_asc'])
                count_query = "SELECT COUNT(*) FROM (SELECT DISTINCT games.game_id, games.name, games.header_image FROM (games INNER JOIN game_category ON games.game_id = game_category.game_id) WHERE games.name LIKE ? AND game_category.category_id IN %s" % (session['categories'],)
        # If words
        else:
            sql_query = "SELECT game_id, name, header_image FROM games WHERE name LIKE ? ORDER BY %s %s LIMIT ? OFFSET ?;" % (session['sort_style'], session['sort_asc'])
            count_query = "SELECT COUNT(*) FROM (SELECT game_id, name, header_image FROM games WHERE name LIKE ?);"
        game_info = select_database(sql_query, (session['search_query'], LIMIT, offset))
        if not session['max_pages']:
            count_query = select_database(count_query, (session['search_query'],))
    else:
        # If genres
        if session['genres'] or session['categories']:
            if session['genres'] and session['categories']:
                sql_query = "SELECT DISTINCT games.game_id, games.name, games.header_image FROM ((games INNER JOIN game_genre ON games.game_id = game_genre.game_id) INNER JOIN game_category ON games.game_id = game_category.game_id) WHERE game_genre.genre_id IN %s AND game_category.category_id IN %s ORDER BY %.8s %.4s LIMIT ? OFFSET ?;" % (session['genres'], session['categories'], session['sort_style'], session['sort_asc'])
                count_query = "SELECT COUNT(*) FROM (SELECT DISTINCT games.game_id, games.name, games.header_image FROM ((games INNER JOIN game_genre ON games.game_id = game_genre.game_id) INNER JOIN game_category ON games.game_id = game_category.game_id) WHERE game_genre.genre_id IN %s AND game_category.category_id IN %s);" % (session['genres'], session['categories'])
            elif session['genres']:
                sql_query = "SELECT DISTINCT games.game_id, games.name, games.header_image FROM (games INNER JOIN game_genre ON games.game_id = game_genre.game_id) WHERE game_genre.genre_id IN %s ORDER BY %.8s %.4s LIMIT ? OFFSET ?;" % (session['genres'], session['sort_style'], session['sort_asc'])
                count_query = "SELECT COUNT(*) FROM (SELECT DISTINCT games.game_id, games.name, games.header_image FROM (games INNER JOIN game_genre ON games.game_id = game_genre.game_id) WHERE game_genre.genre_id IN %s);" % (session['genres'],)
            else:
                sql_query = "SELECT DISTINCT games.game_id, games.name, games.header_image FROM (games INNER JOIN game_category ON games.game_id = game_category.game_id) WHERE game_category.category_id IN %s ORDER BY %.8s %.4s LIMIT ? OFFSET ?;" % (session['categories'], session['sort_style'], session['sort_asc'])
                count_query = "SELECT COUNT(*) FROM (SELECT DISTINCT games.game_id, games.name, games.header_image FROM (games INNER JOIN game_category ON games.game_id = game_category.game_id) WHERE game_category.category_id IN %s);" % (session['categories'],)
        # If blank search
        else:
            sql_query = "SELECT game_id, name, header_image FROM games ORDER BY %.8s %.4s LIMIT ? OFFSET ?;" % (session['sort_style'], session['sort_asc'])
            count_query = "SELECT COUNT(*) FROM (SELECT game_id, name, header_image FROM games);"
        game_info = select_database(sql_query, (LIMIT, offset))
        if not session['max_pages']:
            count_query = select_database(count_query)
    if not session['max_pages']:
        session['max_pages'] = ceil(count_query[0][0] / LIMIT)
    page_form.page_num.validators[0].max = session['max_pages']
    page_form.process()
    return render_template(SEARCH_GAMES, page_form=page_form, form=combined_form, game_info=game_info, max_pages=session['max_pages'], page=session['page'])
    # except Exception as e:
    #     abort(404, e)


@app.route('/favourite_image/<string:username>/<int:game_id>/<int:clicked>', methods=["POST", "GET"])
def favourite_image(username, game_id, clicked):
    favourite_check = FavouriteGames.query.filter_by(user_id=username).all()
    for favourite in favourite_check:
        print(game_id, favourite.game_id)
        if favourite.game_id == game_id:
            if clicked == 1:
                db.session.delete(favourite)
                db.session.commit()
                return render_template(FAV_IMAGE, image="unfavourite", game_id=game_id)
            return render_template(FAV_IMAGE, image="favourite", game_id=game_id)
    if clicked == 1:
        new_favourite = FavouriteGames()
        new_favourite.user_id = username
        new_favourite.game_id = game_id
        db.session.add(new_favourite)
        db.session.commit()
        return render_template(FAV_IMAGE, image="favourite")
    return render_template(FAV_IMAGE, image="unfavourite")


@app.route("/profile_img", methods=["POST"])
@login_required
def profile_img():
    pass


@app.route("/similar_users")
def similar_users():
    pass


@app.route("/game/<int:game_id>")
def single_game(game_id):
    """Individual game information page"""
    class Game():
        """Automatically does SQL queries to build information of a single game"""
        def __init__(self, game_id):
            # Gets basic info from the games table
            game_info = Games.query.filter(Games.game_id == game_id).first()
            self.name = game_info.name
            self.date = game_info.release_date
            self.price = game_info.price
            self.synopsis = game_info.synopsis
            self.header = game_info.header_image
            self.website = game_info.website
            self.notes = game_info.notes
            self.playtime = game_info.playtime
            self.game_id = game_id

        # List of applicable tables :
        # 'genre', 'category', 'tag', 'developer', 'publisher'
        def select_bridge(self, table):
            """Selects genre, category, tag and etc. information"""
            # Gets IDs from associated games' bridge table to use on the corresponding table to get names
            results = select_database("SELECT %.9s_id FROM game_%.9s WHERE game_id = %.9s;" % (table, table, self.game_id))
            # Checks if SELECT statement returned anything, if so, add genre/category/tag/etc.'s name to result_list based off of IDs returned
            if results:
                result_list = []
                for result in results:
                    result_list.append(select_database("SELECT %.9s_name FROM %.9ss WHERE %.9s_id = %.9s;" % (table, table, table, result[0]))[0][0])
                return result_list
            else:
                return None

        def basic_info(self):
            """Returns information from games"""
            return [self.name, self.date, self.price, self.synopsis, self.header, self.website, self.notes, self.playtime]
    selected_game = Game(game_id)
    game_info = selected_game.basic_info()
    genres = selected_game.select_bridge('genre')
    tags = selected_game.select_bridge('tag')
    categories = selected_game.select_bridge('category')
    developers = selected_game.select_bridge('developer')
    publishers = selected_game.select_bridge('publisher')
    return render_template(SELECTED_GAME, game_info=game_info, genres=genres, tags=tags, categories=categories, developers=developers, publishers=publishers)


# Displays all the games the user has tracked/favourited
@app.route("/favourite_games", methods=["POST", "GET"])
@login_required
def favourite_games():
    """Loads all the games the user has favourited"""
    offset = (session['page'] - 1) * LIMIT
    username = current_user.username
    fav_games = FavouriteGames.query.filter_by(user_id=username).limit(LIMIT).offset(offset).all()
    if fav_games:
        id_list = []
        for game in fav_games:
            id_list.append(game.game_id)
        game_info = Games.query.filter(Games.game_id.in_(id_list)).all()
    else:
        game_info = None
    if not session['max_pages']:
        count_query = FavouriteGames.query.filter_by(user_id=username).count()
        session['max_pages'] = ceil(count_query / LIMIT)
    page_form = PageForm()
    page_form.page_num.default = session['page']
    if page_form.validate_on_submit():
        if page_form.page_num.data:
            session['page'] = page_form.page_num.data
            return redirect(url_for('favourite_games'))
        session['page'] = 1
        return redirect(url_for('favourite_games'))
    page_form.page_num.validators[0].max = session['max_pages']
    page_form.process()
    return render_template(FAV_GAME, page_form=page_form, game_info=game_info, max_pages=session['max_pages'], page=session['page'])


if __name__ == "__main__":
    app.run(debug=True)
