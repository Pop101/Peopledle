from flask import Flask, render_template, request
from waitress import serve
from apscheduler.schedulers.background import BackgroundScheduler
from random import choice
from modules.mongrel_db import MongrelDB
from anyascii import anyascii
import hashlib

hash = lambda x: int(hashlib.sha256(repr(x).encode("utf-8")).hexdigest(), 16) # Deterministic hash

MAX_GUESSES = 5
app = Flask(__name__)
db = MongrelDB("./data")
current_day = 1

@app.route("/", methods=["GET"])
def index():
    person = get_person(current_day)
    return render_template("index.html", info=person)


@app.route("/", methods=["POST"])
def post():
    print("GOT GUESS", request.json)
    person = get_person(current_day)
    return {"response": "OK", "result": {"next_hint": person["guesses"][request.json["guesses"]]}}


@app.route("/names", methods=["GET"])
def get_valid_people() -> list[str]:
    """Returns a list of all people in the database.
    Simplifies all unicode characters to ASCII.
    """

    people = list()
    for person in db:
        people.append(anyascii(db[person]["name"]))
    return people


def increment_person():
    global current_day
    
    current_day += 1
    
    # Save to file
    with open("day.txt", "w") as f:
        f.write(str(current_day))

def get_person(day:int):
    person_name = list(db)[hash(day) % len(db)]
    return db[person_name]

if __name__ == "__main__":
    # Try to load current day from file
    # subtract 1 as we increment it later
    # if no file is found, we start at 0
    try:
        with open("day.txt", "r") as f:
            current_day = int(f.read()) - 1
    except FileNotFoundError:
        pass
    increment_person()

    apsched = BackgroundScheduler()
    apsched.start()
    apsched.add_job(increment_person, "cron", day="*", hour="0")

    # Start the server
    print("Starting server on port 8787")
    print(get_person(current_day)["name"])
    # USE WAITRESS IN PRODUCTION: serve(app, host="0.0.0.0", port=8787)
    app.run(debug=True)
