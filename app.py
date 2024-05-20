from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

DATABASE = "gamematch.db"
HOME = "home.html"
GAMES = "games.html"


def connect_database_id(statement, id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(statement, id)
    results = cursor.fetchall()
    conn.close()
    return results


def connect_database(statement):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(statement)
    results = cursor.fetchall()
    conn.close()
    return results


@app.route("/")
def home():
    return render_template(HOME)


@app.route("/games")
def games():
    game_info = connect_database("SELECT game_id, name, release_date, price, synopsis, header_image FROM games;")
    for count, game in enumerate(game_info):
        game = list(game)
        genres = connect_database_id("SELECT genre_id FROM game_genre WHERE game_id = ?;", (game[0],))
        genre_list = []
        for genre in genres:
            genre_list.append(connect_database_id("SELECT genre_name FROM genres WHERE genre_id = ?;", (genre[0]))[0][0])
        game.append(genre_list)
        game_info[count] = game
    print(game_info[0])
    
    return render_template(GAMES)


if __name__ == "__main__":
    app.run(debug=True)