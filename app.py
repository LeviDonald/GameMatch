from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

DATABASE = "gamematch.db"
HOME = "home.html"

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


if __name__ == "__main__":
    app.run(debug=True)