'''Game Match Website'''
import sqlite3
from math import ceil
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import Flask, render_template, abort, url_for, request, redirect, flash
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, DateField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError

app = Flask(__name__)

DATABASE = "gamematch.db"
HOME = "home.html"
GAMES = "games.html"
SEARCH_GAMES = "search.html"
SELECTED_GAME = "selected_game.html"
LOGIN = "login.html"
LOGOUT = "logout.html"
SIGNUP = "signup.html"
FAV_GAME = "favourite_games.html"
ERROR404 = "404.html"
LIMIT = 5

app.config['SECRET_KEY'] = '1e5ec2a58f909c4edbe7ffb3a7dcd84d'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gamematch.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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


class Genres(db.Model):
    """genres SQLAlchemy Table"""
    __table__ = db.Table('genres', db.metadata, autoload_with=epic_engine)


class Publishers(db.Model):
    """publishers SQLAlchemy Table"""
    __table__ = db.Table('publishers', db.metadata, autoload_with=epic_engine)


class Tags(db.Model):
    """tags SQLAlchemy Table"""
    __table__ = db.Table('tags', db.metadata, autoload_with=epic_engine)


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


# WTForm for login.html
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
    submit = SubmitField("Submit")


@login_manager.user_loader
def load_user(user_id):
    """When logging in, gets username"""
    return Users.query.get(str(user_id))


# Redirect here if error occurs
@app.errorhandler(404)
def error_404(exception):
    """Error page"""
    return render_template(ERROR404, exception=exception)


# Home page
@app.route("/")
def home():
    """Home page"""
    return render_template(HOME)


@app.route("/login", methods=["POST", "GET"])
def login():
    """Login form. Checks if username and password is correct and then logs in using flask-wtf"""
    form = LoginForm()
    if form.validate_on_submit():
        user_info = Users.query.filter_by(username=form.username.data).first()
        if user_info:
            if check_password_hash(user_info.password, form.password.data):
                login_user(user_info, remember=True)
                return redirect(url_for('home'))
            else:
                flash("Incorrect username / password")
        else:
            flash("Incorrect username / password")
        return redirect(url_for("home"))
    return render_template(LOGIN, form=form)


@app.route("/signup", methods=["POST", "GET"])
def signup():
    """Sign up form. If user has unique username, encrypt password and add to database"""
    form = SignForm()
    if form.validate_on_submit():
        dob = form.dob.data
        if dob <= (datetime.today() - relativedelta(years=17)).date():
            user_check = Users.query.filter_by(username=form.username.data).first()
            if user_check:
                flash("This username has already been taken! Please use a different one.")
            else:
                user = Users()
                user.username = form.username.data
                user.password = generate_password_hash(form.password.data, salt_length=16)
                db.session.add(user)
                db.session.commit()
                login_user(user, remember=True)
                return redirect(url_for('home'))
        else:
            flash("You must be older than 16 to join this website :'(")
            return redirect(url_for('home'))
    return render_template(SIGNUP, form=form)


@app.route("/logout")
@login_required
def logout():
    """Logs out via. Flask-login and redirects to logout page"""
    logout_user()
    return render_template(LOGOUT)


@app.route("/games/<int:page>/<string:sort_style>/<string:sort_asc>")
def games(page, sort_style, sort_asc):
    """Games page when not searching"""
    offset = (page-1) * LIMIT
    try:
        max_pages = select_database("SELECT COUNT(*) FROM games;")
        max_pages = ceil(max_pages[0][0] / LIMIT)
        if page > max_pages:
            abort(404, "This page doesn't exist!")
        # As the ? substitution does not apply to column names, I have to change the column name manually
        sql_query = "SELECT game_id, name, header_image FROM games ORDER BY %.8s %.4s LIMIT ? OFFSET ?;" % (sort_style, sort_asc)
        game_info = select_database(sql_query, (LIMIT, offset))
        if game_info:
            # Gets genres, categories and tags in alphabetical order to be used in the search menu
            genres = Genres.query.order_by("genre_name").all()
            categories = Categories.query.order_by("category_name").all()
            tags = Tags.query.order_by("tag_name").all()
            return render_template(GAMES, game_info=game_info, page=page, max_pages=max_pages, sort_style=sort_style, sort_asc=sort_asc, genres=genres, categories=categories, tags=tags)
        else:
            abort(404, "This page doesn't exist!")
    except Exception as exception:
        abort(404, exception)



@app.route("/game/<int:game_id>")
def single_game(game_id):
    """Individual game information page"""
    class Game():
        """Automatically does SQL queries to build information of a single game"""
        def __init__(self, game_id):
            # Gets basic info from the games table
            game_info = Games.query.filter(Games.game_id == game_id).first()
            # game_info = select_database("SELECT name, release_date, price, synopsis, header_image, website, notes, playtime FROM games WHERE game_id = ?;", (game_id,))[0]
            self.name = game_info.name
            self.date = game_info.release_date
            # SQLAlchemy annoyingly adds a bunch of random ending 0s to my NUMERIC values
            self.price = round(game_info.price, 2)
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


# Middleman for page changes, gets page num and redirects back to 'games'
@app.route("/number_game/<string:sort_style>/<string:sort_asc>")
def number_game(sort_style, sort_asc):
    """Upon changing page number, get form data for  and then redirect to games"""
    try:
        if request.method == "POST":
            search_number = request.form["page_num"]
        else:
            search_number = request.args.get("page_num")
        return redirect(url_for('games', page=search_number, sort_style=sort_style, sort_asc=sort_asc))
    except Exception as exception:
        abort(404, exception)


# Gateway for page changes, gets page num and redirects back to 'search'
@app.route("/number_search/<string:search_text>/<string:sort_style>/<string:sort_asc>")
def number_search(search_text, sort_style, sort_asc):
    """If searching and user changes page number, get form data for page number and redirect to search"""
    try:
        if request.method == "POST":
            search_number = request.form["page_num"]
        else:
            search_number = request.args.get("page_num")
        return redirect(url_for('search', page=search_number, search_text=search_text, sort_style=sort_style, sort_asc=sort_asc))
    except Exception as exception:
        abort(404, exception)


@app.route("/search/<int:page>", methods=['GET'])
@app.route("/search/<int:page>/<string:search_text>/<string:sort_style>/<string:sort_asc>", methods=['GET'])
def search(page, search_text=None, sort_style=None, sort_asc=None):
    """Same as games but with extra code for searching"""
    try:
        # If search_text exists, don't request args
        if search_text:
            print('hi')
        elif request.method == "GET":
            search_text = request.args.get("search_text")
            sort_style = request.args.get("sort_style")
            sort_asc = request.args.get("sort_asc")
            sort_genres = request.args.getlist("sort_genres")
            sort_tags = request.args.getlist("sort_tags")
            sort_categories = request.args.getlist("sort_categories")
        # If neither request method is GET and no search_text, redirect back to games
        if not search_text:
            return redirect(url_for('games', page=1, sort_style=sort_style, sort_asc=sort_asc))
        offset = (page-1) * LIMIT
        # Manually adding %s to use with SQL's LIKE to find any games that includes the input text
        search_text_query = f'%{search_text}%'
        max_pages = select_database("SELECT COUNT(*) FROM games WHERE name LIKE ?;", (search_text_query,))
        max_pages = ceil(max_pages[0][0] / LIMIT)

        if sort_style == 'playtime':
            if sort_asc == "ASC":
                sort_asc_real = "DESC"
            else:
                sort_asc_real = "ASC"
        else:
            sort_asc_real = sort_asc
        genres = Genres.query.order_by("genre_name").all()
        categories = Categories.query.order_by("category_name").all()
        tags = Tags.query.order_by("tag_name").all()
        sql_query = "SELECT game_id, name, header_image FROM games WHERE name LIKE ? ORDER BY %.8s %.4s LIMIT ? OFFSET ?;" % (sort_style, sort_asc_real)
        search_results = select_database(sql_query, (search_text_query, LIMIT, offset))
        if search_results:
            return render_template(SEARCH_GAMES, game_info=search_results, page=page, max_pages=max_pages, search_text=search_text, sort_style=sort_style, sort_asc=sort_asc, genres=genres, categories=categories, tags=tags)
        else:
            return render_template(SEARCH_GAMES, game_info=None, page=page, max_pages=max_pages, search_text=search_text, sort_style=sort_style, sort_asc=sort_asc, genres=genres, categories=categories, tags=tags)
    except Exception as exception:
        abort(404, exception)


# Displays all the games the user has tracked/favourited
@app.route("/favourite_games/<string:username>")
@login_required
def favourite_games(username):
    """Loads all the games the user has favourited"""
    pass


if __name__ == "__main__":
    app.run(debug=True)
