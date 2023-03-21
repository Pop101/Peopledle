from flask import Flask, render_template, request, abort
from waitress import serve
from apscheduler.schedulers.background import BackgroundScheduler
from modules.mongrel_db import MongrelDB
from modules.determinism import choice, hash, reseed, set_seed
from modules.pagerank_hinter import randomize_const, select
from modules.simplecache import cache, KB
from modules import config, metrics
from modules.edit_distance import edit_distance
from anyascii import anyascii
from time import time
import hashlib

clamp = lambda x, a, b: max(min(x, b), a)

app = Flask(__name__)
db = MongrelDB(config.get("db_path", "./data"))
current_day = 0

@app.route("/", methods=["GET"])
def index():
    return past_people(current_day)

@app.route("/", methods=["POST"])
def post():
    return post_guess(current_day)

@app.route("/<int:day>", methods=["GET"])
def past_people(day:int = 0):
    if not (0 < day <= current_day):
        abort(404)
        
    person = get_person(day)
    return render_template(
        "index.html",
        info = person,
        current_day = current_day,
        get_avg = lambda x: str(round(metrics.get_average(x), 2)),
        version = config.get("version", "unknown"),
        max_guesses = config.get("max_guesses", 5),
    )
                

@app.route("/<int:day>", methods=["POST"])
def post_guess(day:int = 0):
    person = get_person(day)
    
    max_distance = round(len(person["name"]) * 0.05 + 0.4)
    guess_correct = edit_distance(request.json["guess"], person["name"], processor=lambda x: anyascii(x.lower())) < max_distance
    
    for name_part in person["name"].split(" "):
        max_distance = round(len(name_part) * 0.05 + 0.4)
        guess_correct = guess_correct or edit_distance(request.json["guess"], name_part, processor=lambda x: anyascii(x.lower())) < max_distance
    
    hint = '' if guess_correct or request.json["guesses"] >= len(person["guesses"]) else person["guesses"][request.json["guesses"]]
    metrics.record_guess(calc_uid(), day, clamp(request.json["guesses"], 1, len(person["guesses"])), guess_correct)
    return {
        "response": "OK",
        "result": {
            "next_hint": hint,
            "correct": guess_correct
        }
    }


@app.route("/names", methods=["GET"])
def get_valid_people() -> list:
    """Returns a list of all people in the database.
    Simplifies all unicode characters to ASCII.
    """

    people = list()
    for person in db:
        people.append(anyascii(db[person]["name"]))
    return people

def calc_uid(): # not uuid
    if request.headers.get('X-Real-Ip', None):
        ip = request.headers.get('X-Real-Ip', None)
    else:
        ip = request.environ['REMOTE_ADDR']
    
    agent = request.headers.get('User-Agent')
    timestamp = int(round(time()) % (5*60))
    
    return str(hash(f"{ip}{agent}"))[:32]
    

def increment_person():
    global current_day
    
    current_day += 1
    
    # Save to file
    with open("day.txt", "w") as f:
        f.write(str(current_day))

@cache(512 * KB)
def get_person(day:int):
    set_seed(day)
    
    person_name = choice(list(db))
    full_data = db[person_name]
    person = {
        "name": full_data["name"],
        "summary": full_data["summary"],
        "img": full_data["img"],
        "hints": list(filter(lambda x: bool(x), full_data["categories"])),
        "guesses": list(),
    }

    # Generate hints
    ranked_sentences = full_data["sentences"]
    ranked_sentences = randomize_const(ranked_sentences, 0.04)
    ranked_sentences = dict(sorted(ranked_sentences.items(), key=lambda x: x[1]))
    ranked_sentences = dict(filter(lambda x: 30 < len(x[0]) < 400, ranked_sentences.items()))
    
    guesses = select(ranked_sentences, config.get("max_guesses", 5))
    
    # Repeat so a player that "lost" can keep playing
    guesses.extend(x for x in ranked_sentences if x not in guesses)
    
    person["guesses"] = guesses
    
    return person

if __name__ == "__main__":
    # Check if the database is empty
    # If it is, run the scraper
    if len(db) == 0:
        print("Database is empty, running scraper...")
        import wikiscrape
        wikiscrape.main()
    
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

    print("Today's Person:", get_person(current_day)["name"])
    
    # Start the server
    port = config.get("port", 3465)
    if config.get("server debug", False):
        app.run(host='0.0.0.0', port=port, debug=True)
    else:
        print(f"Starting server on http://127.0.0.1:{port}")
        serve(app, host="0.0.0.0", port=port, threads=4)
