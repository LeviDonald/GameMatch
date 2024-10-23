'''Game Match Website'''
from app import app
from sys import exc_info
from math import ceil
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import render_template, abort, url_for, request, redirect, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, LoginManager, login_required, logout_user, current_user
from sqlite3 import connect
from os.path import abspath

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{abspath('app/gamematch.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Disallow image upload sizes beyond 1MB
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.gif']
app.secret_key = '1e5ec2a58f909c4edbe7ffb3a7dcd84d'

db = SQLAlchemy(app)
db.Model.metadata.reflect(db.engine)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

import app.models as models
import app.forms as forms

HOME = "home.html"
SEARCH_GAMES = "search.html"
SELECTED_GAME = "selected_game.html"
LOGIN = "login.html"
LOGOUT = "logout.html"
SIGNUP = "signup.html"
FAV_GAME = "fav_games.html"
FAV_IMAGE = "fav_image.html"
USER_PROFILE = "user_profile.html"
ERROR404 = "404.html"
DATABASE = "app/gamematch.db"
LIMIT = 5


# Easy query process function (TO DO: possibly convert into class)
# Use when using SELECT queries :)
def select_database(query, id=None):
    """Selects raw queries (SELECT)"""
    try:
        conn = connect(DATABASE)
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
        conn = connect(DATABASE)
        cursor = conn.cursor()
        if id:
            cursor.execute(query, id)
        else:
            cursor.execute(query)
        conn.commit()
        conn.close()
    except Exception as exception:
        abort(404, exception)


class DatabaseQuery:
    """Flask SQLAlchemy query builder"""
    def __init__(self, model, join_model, model_args):
        self.model = model
        self.join_model = join_model
        self.model_args = model_args
        self.query = model.query
        return self.query_join()

    def query_join(self):
        if self.model:
            for i in self.join_model:
                self.query = self.query.join(i)
        return self.query_filter()

    def query_filter(self):
        for i in range(len(self.model_args)):
            self.query = self.query.filter(self.model_args[i])
        return self.query_results()

    def query_results(self):
        offset = (session['page'] - 1) * LIMIT
        results = self.query.limit(LIMIT).offset(offset).distinct().all()
        if not session['max_pages']:
            session['max_pages'] = self.query.distinct().count()
        return results


def one_id_bugfix(sort_list):
    """Removes the tuple comma at the end to make SQL not break"""
    # If only one item in tuple
    if len(sort_list) == 1:
        # Remove comma
        sort_list = f"({sort_list[0]})"
    # If multiple items, return full list
    return sort_list


@login_manager.user_loader
def load_user(user_id):
    """When logging in, gets username"""
    return db.session.query(models.Users).filter_by(username=str(user_id)).first()


@app.errorhandler(404)
def error_404(exception):
    """Error 404 page. If error occurs, redirect here w/ exception"""
    exc_type, exc_obj, exc_tb = exc_info()
    return render_template(ERROR404, exception=exception, exc_type=exc_type, exc_obj=exc_obj, exc_tb=exc_tb)


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
    # try:
    form = forms.LoginForm()
    # When form is submitted
    if form.validate_on_submit():
        # Get user information based on input username
        user_info = db.session.query(models.Users).filter_by(username=form.username.data).first()
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
        return redirect(url_for("login"))
    return render_template(LOGIN, form=form)
    # except Exception as e:
    #     abort(404, e)


@app.route("/signup", methods=["POST", "GET"])
def signup():
    """Sign up form. If user has unique username, encrypt password and add to database"""
    try:
        form = forms.SignForm()
        if form.validate_on_submit():
            dob = form.dob.data
            # If user is older than 17 years old (as users are given the possibility to chat through sharing discord info, I put an age limit)
            if dob <= (datetime.today() - relativedelta(years=17)).date():
                # If a result from the DB comes back then the username has already been taken
                user_check = db.session.query(models.Users).filter_by(username=form.username.data).first()
                if user_check:
                    flash("This username has already been taken! Please use a different one.")
                else:
                    # Else, set up a new user with the input username and newly generated hash
                    user = models.Users()
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
    """Makes sure upon going to games page, previous search queries are refreshed."""
    try:
        session['page'] = 1
        session['genres'] = None
        session['categories'] = None
        session['sort_style'] = 'name'
        session['sort_asc'] = 'ASC'
        session['search_query'] = None
        session['max_pages'] = None
        if fav == 1:
            return redirect(url_for('favourite_list'))
        return redirect(url_for('games'))
    except Exception as e:
        abort(404, e)


@app.route("/change_page/<int:page>/<int:fav>")
def change_page(page, fav):
    """Checks if new page change is an acceptable number, changes page."""
    try:
        # To prevent people from just altering the page in the search bar to a non-existant page
        if page <= session['max_pages'] and page > 0:
            session['page'] = page
            if fav == 1:
                return redirect(url_for('favourite_list'))
            return redirect(url_for('games'))
    except Exception as e:
        abort(404, e)


@app.route("/games", methods=["POST", "GET"])
def games():
    """Manages WTForm data for genres / categories. Returns data from 'games' table in database."""
    # Sets offset for SQL statement by getting current page and multiplying it by the limit
    offset = (session['page'] - 1) * LIMIT
    page_form = forms.PageForm()
    combined_form = forms.CombinedForm()
    # Sets the information for the genres / categories form using SQLAlchemy
    combined_form.gen_form.genres.query = db.session.query(models.Genres).all()
    combined_form.gen_form.categories.query = db.session.query(models.Categories).all()
    # Assigns the default number for the page change part of my code as the current page
    page_form.page_num.default = session['page']
    # Manually inserts choices to style and asc/desc
    combined_form.sort_form.sort_style.choices = [('name', 'Alphabetically'), ('playtime', 'Popularity')]
    combined_form.sort_form.sort_asc.choices = [('ASC', 'Ascending'), ('DESC', 'Descending')]
    if page_form.validate_on_submit():
        # Check if the user has put in an actual input
        if page_form.page_num.data:
            # Make session['page'] = new page
            session['page'] = page_form.page_num.data
            return redirect(url_for('games'))
    # Originally wasn't working before so I used submit but .validate_on_submit
    # works as well.
    if combined_form.is_submitted() and 'combined' in request.form:
        # Reset previous query + max pages as max pages will change
        # with the new query.
        session['search_query'] = None
        session['max_pages'] = None
        # Switches ASC and DESC around because popularity ascending
        # will return games from the least popular to the most popular
        # and Popularity ascending is just more logical
        if combined_form.sort_form.sort_style.data == "playtime":
            if combined_form.sort_form.sort_asc.data == "ASC":
                combined_form.sort_form.sort_asc.data = "DESC"
            else:
                combined_form.sort_form.sort_asc.data = "ASC"
        # Can't put in function format because of unique column names (e.g genre_id)
        genres = combined_form.gen_form.genres.data
        categories = combined_form.gen_form.categories.data
        # In order to use the IN keyword in SQL statements, the data type must be a tuple
        if genres or categories:
            new_list = []
            if genres:
                # Sorts form data into list
                for genre in genres:
                    new_list.append(genre.genre_id)
                # If only one item in list, there won't be an ending ',' at the end
                # Therefore I made the one_id_bugfix function
                session['genres'] = one_id_bugfix(tuple(new_list))
            new_list = []
            if categories:
                # Same as genres but for categories
                for category in categories:
                    new_list.append(category.category_id)
                session['categories'] = one_id_bugfix(tuple(new_list))
        else:
            session['genres'] = None
            session['categories'] = None
        # Assigns sorting options to session
        session['sort_style'] = combined_form.sort_form.sort_style.data
        session['sort_asc'] = combined_form.sort_form.sort_asc.data
        search_query = combined_form.sort_form.search_query.data
        if search_query:
            session['search_query'] = f"%{search_query}%"
        # Because this is a new query, page is set to 1 to prevent crashes
        session['page'] = 1
        return redirect(url_for('games'))
    # If user is searching using words
    if session['search_query']:
        # If words + genres
        if session['genres'] or session['categories']:
            if session['genres'] and session['categories']:
                # sql_query = DatabaseQuery(models.Games, join_model=(models.GameGen.game_id, models.GameCat.game_id), model_args=(models.Games.name.like(session['search_query']), models.GameGen.genre_id.in_(session['genres']), models.GameCat.category_id.in_(session['categories'])))
                # sql_query = db.session.query(models.Games, models.GameGen, models.GameCat).filter(models.Games.game_id == models.GameGen.game_id).filter(models.Games.game_id == models.GameCat.game_id).filter(models.Games.name.like(session['search_query'])).filter(models.GameGen.genre_id.in_(session['genres'])).filter(models.GameCat.category_id.in_(session['categories'])).limit(LIMIT).offset(offset).distinct()
                sql_query = "SELECT DISTINCT games.game_id, games.name, games.header_image FROM ((games INNER JOIN game_genre ON games.game_id = game_genre.game_id) INNER JOIN game_category ON games.game_id = game_category.game_id) WHERE games.name LIKE ? AND game_genre.genre_id IN %s AND game_category.category_id IN %s ORDER BY %.8s %.4s LIMIT ? OFFSET ?;" % (session['genres'], session['categories'], session['sort_style'], session['sort_asc'])
                count_query = "SELECT COUNT(DISTINCT games.game_id) FROM ((games INNER JOIN game_genre ON games.game_id = game_genre.game_id) INNER JOIN game_category ON games.game_id = game_category.game_id) WHERE games.name LIKE ? AND game_genre.genre_id IN %s AND game_category.category_id IN %s;" % (session['genres'], session['categories'])
            elif session['genres']:
                sql_query = "SELECT DISTINCT games.game_id, games.name, games.header_image FROM (games INNER JOIN game_genre ON games.game_id = game_genre.game_id) WHERE games.name LIKE ? AND game_genre.genre_id IN %s ORDER BY %.8s %.4s LIMIT ? OFFSET ?;" % (session['genres'], session['sort_style'], session['sort_asc'])
                count_query = "SELECT COUNT(DISTINCT games.game_id) FROM (games INNER JOIN game_genre ON games.game_id = game_genre.game_id) WHERE games.name LIKE ? AND game_genre.genre_id IN %s" % (session['genres'],)
            else:
                sql_query = "SELECT DISTINCT games.game_id, games.name, games.header_image FROM (games INNER JOIN game_category ON games.game_id = game_category.game_id) WHERE games.name LIKE ? AND game_category.category_id IN %s ORDER BY %.8s %.4s LIMIT ? OFFSET ?;" % (session['categories'], session['sort_style'], session['sort_asc'])
                count_query = "SELECT COUNT(DISTINCT games.game_id) FROM (games INNER JOIN game_category ON games.game_id = game_category.game_id) WHERE games.name LIKE ? AND game_category.category_id IN %s" % (session['categories'],)
        # If words
        else:
            sql_query = "SELECT game_id, name, header_image FROM games WHERE name LIKE ? ORDER BY %s %.4s LIMIT ? OFFSET ?;" % (session['sort_style'], session['sort_asc'])
            count_query = "SELECT DISTINCT COUNT(games.game_id) FROM games WHERE name LIKE ?;"
        game_info = select_database(sql_query, (session['search_query'], LIMIT, offset))
        if not session['max_pages']:
            count_query = select_database(count_query, (session['search_query'],))
    else:
        # If genres
        if session['genres'] or session['categories']:
            if session['genres'] and session['categories']:
                sql_query = "SELECT DISTINCT games.game_id, games.name, games.header_image FROM ((games INNER JOIN game_genre ON games.game_id = game_genre.game_id) INNER JOIN game_category ON games.game_id = game_category.game_id) WHERE game_genre.genre_id IN %s AND game_category.category_id IN %s ORDER BY %.8s %.4s LIMIT ? OFFSET ?;" % (session['genres'], session['categories'], session['sort_style'], session['sort_asc'])
                count_query = "SELECT COUNT(DISTINCT games.game_id) FROM ((games INNER JOIN game_genre ON games.game_id = game_genre.game_id) INNER JOIN game_category ON games.game_id = game_category.game_id) WHERE game_genre.genre_id IN %s AND game_category.category_id IN %s;" % (session['genres'], session['categories'])
            elif session['genres']:
                sql_query = "SELECT DISTINCT games.game_id, games.name, games.header_image FROM (games INNER JOIN game_genre ON games.game_id = game_genre.game_id) WHERE game_genre.genre_id IN %s ORDER BY %.8s %.4s LIMIT ? OFFSET ?;" % (session['genres'], session['sort_style'], session['sort_asc'])
                count_query = "SELECT COUNT(DISTINCT games.game_id) FROM (games INNER JOIN game_genre ON games.game_id = game_genre.game_id) WHERE game_genre.genre_id IN %s;" % (session['genres'],)
            else:
                sql_query = "SELECT DISTINCT games.game_id, games.name, games.header_image FROM (games INNER JOIN game_category ON games.game_id = game_category.game_id) WHERE game_category.category_id IN %s ORDER BY %.8s %.4s LIMIT ? OFFSET ?;" % (session['categories'], session['sort_style'], session['sort_asc'])
                count_query = "SELECT COUNT(DISTINCT games.game_id) FROM (games INNER JOIN game_category ON games.game_id = game_category.game_id) WHERE game_category.category_id IN %s;" % (session['categories'],)
        # If blank search
        else:
            sql_query = "SELECT game_id, name, header_image FROM games ORDER BY %.8s %.4s LIMIT ? OFFSET ?;" % (session['sort_style'], session['sort_asc'])
            count_query = "SELECT COUNT(DISTINCT games.game_id) FROM games;"
        # game_info[0] - ID, [1] - Name, [2] - Image link
        game_info = select_database(sql_query, (LIMIT, offset))
        # Prevents code having to make additional operations
        # on every page change
        if not session['max_pages']:
            count_query = select_database(count_query)
    if not session['max_pages']:
        session['max_pages'] = ceil(count_query[0][0] / LIMIT)
    page_form.page_num.validators[0].max = session['max_pages']
    page_form.process()
    if current_user.is_authenticated:
        favourite_list = []
        favourites = db.session.query(models.FavouriteGames).filter(models.FavouriteGames.user_id == current_user.user_id).all()
        for favourite in favourites:
            favourite_list.append(favourite.game_id)
        return render_template(SEARCH_GAMES, page_form=page_form, form=combined_form, game_info=game_info, max_pages=session['max_pages'], page=session['page'], fav_list=favourite_list)
    return render_template(SEARCH_GAMES, page_form=page_form, form=combined_form, game_info=game_info, max_pages=session['max_pages'], page=session['page'])


@app.route('/favourite_image/<int:user_id>/<int:game_id>/<int:clicked>', methods=["POST", "GET"])
def favourite_image(user_id, game_id, clicked):
    """Updates favourite games in database. Returns an image depending if an image is favourited or not."""
    favourite_check = db.session.query(models.FavouriteGames).filter_by(user_id=int(user_id)).all()
    for favourite in favourite_check:
        if favourite.game_id == game_id:
            if clicked == 1:
                # PyLint doesn't work well with FlaskSQLAlchemy
                db.session.delete(favourite)
                db.session.commit()
                return render_template(FAV_IMAGE, image="unfavourite", game_id=game_id)
            return render_template(FAV_IMAGE, image="favourite", game_id=game_id)
    if clicked == 1:
        new_favourite = models.FavouriteGames()
        # Using FlaskSQLAlchemy, easily create an instance of FavouriteGames
        # Add filled in instances to database
        new_favourite.user_id = user_id
        new_favourite.game_id = game_id
        db.session.add(new_favourite)
        db.session.commit()
        return render_template(FAV_IMAGE, image="favourite", game_id=game_id)
    return render_template(FAV_IMAGE, image="unfavourite", game_id=game_id)


@app.route('/favourite_game/<int:game_id>/<int:link_id>', methods=["POST"])
def favourite_game(game_id, link_id):
    """Updates favourite_list in database"""
    game_check = db.session.query(models.Games).filter_by(game_id=game_id).first()
    if game_check:
        favourite_check = db.session.query(models.FavouriteGames).filter_by(user_id=current_user.user_id).filter_by(game_id=game_id).first()
        if favourite_check:
            flash(f"Unfavourited {game_check.name}!")
            db.session.delete(favourite_check)
        else:
            favourite = models.FavouriteGames()
            favourite.user_id = current_user.user_id
            favourite.game_id = game_id
            # For some dumb reason, SQLAlchemy cannot detect autoincrement
            # so I need to find the latest ID manually
            id_check = db.session.query(models.FavouriteGames).order_by(models.FavouriteGames.favourite_id.desc()).first()
            if id_check:
                favourite.favourite_id = int(id_check.favourite_id) + 1
            else:
                favourite.favourite_id = 1
            db.session.add(favourite)
        db.session.commit()
        flash(f"Favourited {game_check.name}!")
        if link_id == 0:
            return redirect(url_for('games'))
        elif link_id == 1:
            return redirect(url_for('favourite_list'))
        else:
            return redirect(url_for('single_game', game_id=game_id))
    else:
        flash("Game with that ID does not exist!")
        return redirect(url_for('home'))


@app.route("/profile/<int:user_id>")
def profile(user_id):
    """View users profiles"""
    follow_form = forms.FollowForm()
    user_data = db.session.query(models.Users).filter_by(user_id=user_id).first()
    return render_template(USER_PROFILE, username=user_data.username, pfp=user_data.pfp, about_me=user_data.about, discord=user_data.discord)


@app.route("/profile-edit", methods=["POST"])
@login_required
def profile_edit():
    """Profile management"""
    pfp_form = forms.ProfileForm()
    if pfp_form.validate_on_submit():
        pfp_file = pfp_form.img_file.data
        pfp_file.file_name = secure_filename(current_user.username)


@app.route("/game/<int:game_id>")
def single_game(game_id):
    """Individual game information page"""
    class Game():
        """Automatically does SQL queries to build information of a single game"""
        def __init__(self, game_id):
            # Gets basic info from the games table
            game_info = db.session.query(models.Games).filter(models.Games.game_id == game_id).first()
            self.name = game_info.name
            self.date = game_info.release_date
            self.price = game_info.price
            self.synopsis = game_info.synopsis
            self.header = game_info.header_image
            self.website = game_info.website
            self.notes = game_info.notes
            self.playtime = game_info.playtime
            self.game_id = game_id

        def select_bridge(self, table):
            """Selects genre, category, tag and etc. information"""
            # Gets IDs from associated games' bridge table to use on the corresponding table to get names
            results = select_database("SELECT %.9s_id FROM game_%.9s WHERE game_id = %.9s;" % (table, table, self.game_id))
            # Checks if SELECT statement returned anything; if so, add genre/category/etc.'s name to result_list based off of IDs returned
            if results:
                result_list = []
                for result in results:
                    result_list.append(select_database("SELECT %.9s_name FROM %.9ss WHERE %.9s_id = %.9s;" % (table, table, table, result[0]))[0][0])
                return result_list
            else:
                return None

    selected_game = Game(game_id)
    genres = selected_game.select_bridge('genre')
    categories = selected_game.select_bridge('category')
    developers = selected_game.select_bridge('developer')
    publishers = selected_game.select_bridge('publisher')
    if current_user.is_authenticated:
        favourite_list = []
        favourites = db.session.query(models.FavouriteGames).filter(models.FavouriteGames.user_id == current_user.user_id).all()
        for favourite in favourites:
            favourite_list.append(favourite.game_id)
        return render_template(SELECTED_GAME, game_info=selected_game, genres=genres, categories=categories, developers=developers, publishers=publishers, fav_list=favourite_list)
    return render_template(SELECTED_GAME, game_info=selected_game, genres=genres, categories=categories, developers=developers, publishers=publishers)


@app.route("/favourite_list", methods=["POST", "GET"])
@login_required
def favourite_list():
    """Loads all the games the user has favourited"""
    # Calculates offset for SQL based off of current page times limit
    offset = (session['page'] - 1) * LIMIT
    # Returns all instances of games that the current user has favourited
    fav_games = db.session.query(models.FavouriteGames).filter_by(user_id=current_user.user_id).limit(LIMIT).offset(offset).all()
    # If any favourites at all, get ids and then return all games
    if fav_games:
        id_list = []
        for game in fav_games:
            id_list.append(game.game_id)
        game_info = db.session.query(models.Games).filter(models.Games.game_id.in_(id_list)).all()
    else:
        game_info = None
    # If max_pages hasn't been set yet
    if not session['max_pages']:
        # Return count of all games
        count_query = db.session.query(models.FavouriteGames).filter_by(user_id=current_user.user_id).count()
        # Divides amount of games by limit to get max pages
        session['max_pages'] = ceil(count_query / LIMIT)
    page_form = forms.PageForm()
    page_form.page_num.default = session['page']
    if page_form.validate_on_submit():
        if page_form.page_num.data:
            session['page'] = page_form.page_num.data
            return redirect(url_for('favourite_list'))
        session['page'] = 1
        return redirect(url_for('favourite_list'))
    page_form.page_num.validators[0].max = session['max_pages']
    page_form.process()
    favourite_list = []
    favourites = db.session.query(models.FavouriteGames).filter(models.FavouriteGames.user_id == current_user.user_id).all()
    for favourite in favourites:
        favourite_list.append(favourite.game_id)
    return render_template(FAV_GAME, fav_list=favourite_list, page_form=page_form, game_info=game_info, max_pages=session['max_pages'], page=session['page'])


if __name__ == "__main__":
    app.run(debug=True)
