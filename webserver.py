from functools import wraps
from flask import Flask, render_template, request
from waitress import serve
from apscheduler.schedulers.background import BackgroundScheduler
from json import load
from random import choice
import requests
from re import sub, search, finditer, IGNORECASE
from time import time
from modules.mongrel_db import MongrelDB
from anyascii import anyascii

MAX_GUESSES = 5

app = Flask(__name__)
db = MongrelDB("./data")
data = {"response": "OK", "guess": 2, "result": {"solved": False, "next_hint": "This is a hint"}}


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", language=language["name"].title())


@app.route("/", methods=["POST"])
def post():
    print("GOT GUESS", request.json)
    return data


@app.route("/names", methods=["GET"])
def get_valid_people() -> list[str]:
    people = list()
    for person in db:
        people.append(anyascii(db[person]["name"]))
    return people


def pick_person():
    global person

    def single_pick():
        full_data = db[choice(list(db))]

        person = {
            "name": full_data["name"],
            "summary": full_data["summary"],
            "hints": list(filter(lambda x: bool(x), full_data["category"])),
            "guesses": list(),
        }

        # Split sentences list into equal parts
        # Choose a sentence from each part
        summary = person["summary"]
        summary = list(filter(lambda x: len(x) < 400, summary))
        if len(summary) < MAX_GUESSES:
            return False

        chunk_size = len(person["summary"]) // MAX_GUESSES
        for i in range(MAX_GUESSES):
            person["guesses"].insert(0, choice(summary[i * chunk_size : (i + 1) * chunk_size]))

        return person

    i, person = 0, None
    while i < 100 and not person:
        person = single_pick()
        i += 1

    return person


if __name__ == "__main__":
    pick_person()

    apsched = BackgroundScheduler()
    apsched.start()
    apsched.add_job(pick_person, "cron", day="*", hour="0")

    with app.test_client() as c:
        rv = c.post("/submit", json=data)
        pass

    print("Starting server on port 8787")
    print(language)
    # serve(app, host="0.0.0.0", port=8787)
    app.run(debug=True)
