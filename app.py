from flask import Flask, render_template, abort, url_for
import sqlite3
import requests
from math import ceil

app = Flask(__name__)

DATABASE = "gamematch.db"
HOME = "home.html"
GAMES = "games.html"
ERROR404 = "404.html"


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


@app.errorhandler(404)
def error_404(exception):
    return render_template(ERROR404, exception=exception)


@app.route("/")
def home():
    return render_template(HOME)


@app.route("/games/<int:page>")
def games(page):
    limit = 5
    offset = (page-1)*10
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
        "Accept-Encoding": "*",
        "Connection": "keep-alive"
    }
    try:
        max_pages = connect_database("SELECT COUNT(*) FROM games;")
        max_pages = ceil(max_pages[0][0] / limit)
        # 0 - ID, 1 - Name, 2 - Release, 3 - Price, 4 - Synopsis, 5 - Image, 6 - Genres
        game_info = connect_database_id("SELECT game_id, name, release_date, price, synopsis, header_image FROM games LIMIT ? OFFSET ?;", (limit, offset))
        for count, game in enumerate(game_info):
            game = list(game)
            genres = connect_database_id("SELECT genre_id FROM game_genre WHERE game_id = ?;", (game[0],))
            genre_list = []
            for genre in genres:
                genre_list.append(connect_database_id("SELECT genre_name FROM genres WHERE genre_id = ?;", (genre[0],))[0][0])
            game.append(genre_list)
            # img_data = requests.get(game[5], headers=headers).content
            # with open(f'static/images/{count}.jpg', 'wb') as handler:
            #     handler.write(img_data)
            game_info[count] = game
        return render_template(GAMES, game_info=game_info, page=page, max_pages=max_pages)
    except Exception as e:
        abort(404, e)


if __name__ == "__main__":
    app.run(debug=True)

if __name__ == "__main__":
    app.run(debug=True)