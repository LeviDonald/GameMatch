from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

DATABASE = "gamematch.db"
HOME = "home.html"
GAMES = "games.html"


def connect_database_id(query, id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(query, id)
    results = cursor.fetchall()
    conn.close()
    return results


def connect_database(query):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results


@app.route("/")
def home():
    return render_template(HOME)


@app.route("/games/<int:page>")
def games(page):
    limit = 10
    offset = (page-1)*10
    game_info = connect_database_id("SELECT game_id, name, release_date, price, synopsis, header_image FROM games LIMIT ? OFFSET ?;", (limit, offset))
    for count, game in enumerate(game_info):
        game = list(game)
        genres = connect_database_id("SELECT genre_id FROM game_genre WHERE game_id = ?;", (game[0],))
        genre_list = []
        for genre in genres:
            genre_list.append(connect_database_id("SELECT genre_name FROM genres WHERE genre_id = ?;", (genre[0],))[0][0])
        game.append(genre_list)
        game_info[count] = game
    return render_template(GAMES, game_info=game_info, page=page)


if __name__ == "__main__":
    app.run(debug=True)