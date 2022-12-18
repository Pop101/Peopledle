from functools import wraps
from flask import Flask, render_template, request
from waitress import serve
from apscheduler.schedulers.background import BackgroundScheduler
from json import load
from random import choice
import requests
from re import sub, search, finditer, IGNORECASE
from time import time

app = Flask(__name__)

data = {"response": "OK", "guess": 2, "result": {"solved": False, "next_hint": "This is a hint"}}


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", language=language["name"].title())


@app.route("/", methods=["POST"])
def post():
    print("GOT GUESS", request.json)
    return data


def pick_language():
    global language
    with open("languages.json") as f:
        langs = load(f)

    language = choice(langs)


if __name__ == "__main__":
    pick_language()

    apsched = BackgroundScheduler()
    apsched.start()

    apsched.add_job(pick_language, "cron", day="*", hour="0")

    with app.test_client() as c:
        rv = c.post("/submit", json={"code": 'print "hello world"', "other": "data"})
        pass

    print("Starting server on port 8787")
    print(language)
    # serve(app, host="0.0.0.0", port=8787)
    app.run(debug=True)
