from flask import Flask, render_template, request
from waitress import serve
from apscheduler.schedulers.background import BackgroundScheduler
from random import choice
from modules.mongrel_db import MongrelDB
from anyascii import anyascii

MAX_GUESSES = 5

app = Flask(__name__)
db = MongrelDB("./data")
data = {"response": "OK", "guess": 2, "result": {"solved": False, "next_hint": "This is a hint"}}
person = dict()


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/", methods=["POST"])
def post():
    print("GOT GUESS", request.json)
    return data


@app.route("/names", methods=["GET"])
def get_valid_people() -> list[str]:
    """Returns a list of all people in the database.
    Simplifies all unicode characters to ASCII.
    """

    people = list()
    for person in db:
        people.append(anyascii(db[person]["name"]))
    return people


def pick_person():
    """Pick a random person from the database,
    populating the global variable `person` with their data.

    This function is called on startup and every day at local midnight.

    Returns:
        _type_: _description_
    """
    global person

    # Subfunction to pick a single person
    # Returns JSPON object with that person's data
    #    or False if that person was invalid
    def single_pick():
        full_data = db[choice(list(db))]

        person = {
            "name": full_data["name"],
            "summary": full_data["summary"],
            "hints": list(filter(lambda x: bool(x), full_data["categories"])),
            "guesses": list(),
        }

        # Split sentences list into equal parts
        # Choose a sentence from each part
        summary = full_data["sentences"]
        summary = list(filter(lambda x: len(x) < 400, summary))
        if len(summary) < MAX_GUESSES:
            return False

        chunk_size = len(summary) // MAX_GUESSES
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

    # Quick endpoint integrity test
    with app.test_client() as c:
        rv = c.post("/submit", json=data)
        pass

    # Start the server
    print("Starting server on port 8787")
    print(person)
    # USE WAITRESS IN PRODUCTION: serve(app, host="0.0.0.0", port=8787)
    app.run(debug=True)
