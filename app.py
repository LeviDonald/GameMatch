from flask import Flask, render_template, abort, url_for, request, redirect
import sqlite3
from math import ceil

app = Flask(__name__)

DATABASE = "gamematch.db"
HOME = "home.html"
GAMES = "games.html"
SEARCH_GAMES = "search.html"
SELECTED_GAME = "selected_game.html"
ERROR404 = "404.html"
LIMIT = 5


# Easy query process function (TO DO: possibly convert into class)
# Use when using SELECT queries :)
def select_database(query, id=None):
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
    except Exception as e:
        abort(404, e)


# Use when using queries which include:
# UPDATE, DROP, DELETE, INSERT and etc.
def commit_database(query, id=None):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        if id:
            cursor.execute(query, id)
        else:
            cursor.execute(query)
        conn.commit()
        conn.close()
    except Exception as e:
        abort(404, e)


# Column names in 'games' table to sort by
def sort_name(sort_style):
    match sort_style:
        case 1:
            return "name"
        case 2:
            return "average_playtime"
# Manually convert ANSI data to UTF-8 (Japanese characters didn't load :( )

# def ansi_to_utf(table_name):
#     # Get contents from argument table
#     contents = select_database("SELECT * FROM {};".format(table_name))
#     # Get all columns from specified table
#     columns = select_database("PRAGMA table_info({});".format(table_name))
#     column_table = []
#     # Put column names into table
#     for i in columns:
#         column_table.append(i[1])
#     # Sorting per each item in table
#     for content in contents:
#         # Sorting per each column of item
#         for count, item in enumerate(content):
#             # If not none, convert item text / int from ANSII to UTF-8 manually :)
#             if item and type(item) is str:
#                 item = item.encode("ANSI").decode("utf-8")
#                 # Update table_name and set current column to utf-8 based text where game_id = current game's id
#                 commit_database('UPDATE {} SET {} = "{}" WHERE {} = {};'.format(table_name, column_table[count], item, column_table[0], content[0]))

# ansi_to_utf("developers")


# Use to remove inappropriate tags / genres
def remove_bad_games(ids, name):
    # Goes through each inappropriate ID
    for i in ids:
        # Gets every game ID which is associated with this tag
        bad_games = select_database("SELECT {}_id FROM game_tag WHERE {}_id = ?;".format(name, name), (i,))
        # Removes each bad game from games
        for game in bad_games:
            commit_database("DELETE FROM games WHERE game_id = ?;", (game[0],))
        # Disposes of unnecessary data from bridge table
        commit_database("DELETE FROM game_{} WHERE {}_id = ?".format(name, name), (i,))


# Manually erase games that use bad words
# bad_games = select_database("SELECT game_id FROM games WHERE notes LIKE '%(BAD WORD GOES HERE)%';")
# for i in bad_games:
#     commit_database("DELETE FROM games WHERE game_id = ?;", (i[0],))
# print("don")


@app.errorhandler(404)
def error_404(exception):
    return render_template(ERROR404, exception=exception)


@app.route("/")
def home():
    return render_template(HOME)


@app.route("/games/<int:page>/<int:sort_style>")
def games(page, sort_style):
    offset = (page-1) * LIMIT
    try:
        max_pages = select_database("SELECT COUNT(*) FROM games;")
        max_pages = ceil(max_pages[0][0] / LIMIT)
        if page > max_pages:
            abort(404, "This page doesn't exist!")
        sort_name_ = sort_name(sort_style)
        # 0 - ID, 1 - Name, 2 - Image
        game_info = select_database("SELECT game_id, name, header_image FROM games ORDER BY ? DESC LIMIT ? OFFSET ?;", (sort_name_, LIMIT, offset))
        if game_info:
            # for count, game in enumerate(game_info):
            #     game = list(game)
            #     genres = select_database("SELECT genre_id FROM game_genre WHERE game_id = ?;", (game[0],))
            #     genre_list = []
            #     for genre in genres:
            #         genre_list.append(select_database("SELECT genre_name FROM genres WHERE genre_id = ?;", (genre[0],))[0][0])
            #     game.append(genre_list)
            #     game_info[count] = game
            return render_template(GAMES, game_info=game_info, page=page, max_pages=max_pages, sort_style=sort_style)
        else:
            abort(404, "This page doesn't exist!")
    except Exception as e:
        abort(404, e)


@app.route("/game/<int:game_id>")
def single_game(game_id):
    class game():
        def __init__(self, game_id):
            # Gets basic info from the games table
            game_info = select_database("SELECT name, release_date, price, synopsis, header_image, website, notes, average_playtime FROM games WHERE game_id = ?;", (game_id,))[0]
            self.name = game_info[0]
            self.date = game_info[1]
            self.price = game_info[2]
            self.synopsis = game_info[3]
            self.header = game_info[4]
            self.website = game_info[5]
            self.notes = game_info[6]
            self.average_playtime = game_info[7]
            self.game_id = game_id

        # List of applicable tables :
        # 'genre', 'category', 'tag', 'developer', 'publisher'
        def select_bridge(self, table):
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
            return [self.name, self.date, self.price, self.synopsis, self.header, self.website, self.notes, self.average_playtime]
    selected_game = game(game_id)
    game_info = selected_game.basic_info()
    genres = selected_game.select_bridge('genre')
    tags = selected_game.select_bridge('tag')
    categories = selected_game.select_bridge('category')
    developers = selected_game.select_bridge('developer')
    publishers = selected_game.select_bridge('publisher')
    return render_template(SELECTED_GAME, game_info=game_info, genres=genres, tags=tags, categories=categories, developers=developers, publishers=publishers)


# Gateway for page changes, gets page num and redirects back to 'games'
@app.route("/number_game")
def number_game():
    try:
        if request.method == "POST":
            search_number = request.form.get("page_num")
        else:
            search_number = request.args.get("page_num")
        return redirect(url_for('games', page=search_number))
    except Exception as e:
        abort(404, e)


# Gateway for page changes, gets page num and redirects back to 'search'
@app.route("/number_search/<string:search_text>")
def number_search(search_text):
    try:
        if request.method == "POST":
            search_number = request.form.get("page_num")
        else:
            search_number = request.args.get("page_num")
        return redirect(url_for('search', page=search_number, search_text=search_text))
    except Exception as e:
        abort(404, e)


# Searching for specific games using search box
@app.route("/search/<int:page>", methods=['GET'])
@app.route("/search/<int:page>/<string:search_text>", methods=['GET'])
def search(page, search_text=None):
    try:
        if search_text:
            search_text = search_text
        elif request.method == "GET":
            search_text = request.args.get("search_text")
        if not search_text:
            return redirect(url_for('games', page=1))
        offset = (page-1) * LIMIT
        search_text_query = f'%{search_text}%'
        max_pages = select_database("SELECT COUNT(*) FROM games WHERE name LIKE ?;", (search_text_query,))
        max_pages = ceil(max_pages[0][0] / LIMIT)
        search_results = select_database("SELECT game_id, name, header_image FROM games WHERE name LIKE ? ORDER BY average_playtime DESC LIMIT ? OFFSET ?;", (search_text_query, LIMIT, offset))
        # [0] - Game ID, [1] - Name, [2] - Image
        if search_results:
            # for count, game in enumerate(search_results):
            #     game = list(game)
            #     genres = select_database("SELECT genre_id FROM game_genre WHERE game_id = ?;", (game[0],))
            #     genre_list = []
            #     for genre in genres:
            #         genre_list.append(select_database("SELECT genre_name FROM genres WHERE genre_id = ?;", (genre[0],))[0][0])
            #     game.append(genre_list)
            #     search_results[count] = game
            return render_template(SEARCH_GAMES, game_info=search_results, page=page, max_pages=max_pages, search_text=search_text)
        else:
            return render_template(SEARCH_GAMES, game_info=None, page=page, max_pages=max_pages, search_text=search_text)
    except Exception as e:
        abort(404, e)


if __name__ == "__main__":
    app.run(debug=True)