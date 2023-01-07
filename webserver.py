from flask import Flask, render_template, request, abort
from waitress import serve
from apscheduler.schedulers.background import BackgroundScheduler
from modules.mongrel_db import MongrelDB
from modules import config, metrics
from anyascii import anyascii
from time import time
import hashlib

hash = lambda x: int(hashlib.sha256(repr(x).encode("utf-8")).hexdigest(), 16) # Deterministic hash
choice = lambda x, i: x[hash(i) % len(x)] # Deterministic choice
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
    )
                

@app.route("/<int:day>", methods=["POST"])
def post_guess(day:int = 0):
    person = get_person(day)
    
    guess_correct = request.json["guess"].lower() == person["name"].lower() or anyascii(request.json["guess"].lower()) == anyascii(person["name"].lower())
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

def get_person(day:int):
    person_name = list(db)[hash(day) % len(db)]
    full_data = db[person_name]
    person = {
        "name": full_data["name"],
        "summary": full_data["summary"],
        "img": full_data["img"],
        "hints": list(filter(lambda x: bool(x), full_data["categories"])),
        "guesses": list(),
    }

    # Split sentences list into equal parts
    # Choose a sentence from each part
    summary = full_data["sentences"]
    summary = list(filter(lambda x: len(x) < 400, summary))
    if len(summary) < config.get("max_guesses", 5):
        return False
    
    # Repeat so a player that "lost" can keep playing
    while len(summary) > config.get("max_guesses", 5):
        # Pick a guess from each chunk
        chunk_size = len(summary) // config.get("max_guesses", 5)
        for i in range(config.get("max_guesses", 5)):
            guess = choice(summary[i * chunk_size : (i + 1) * chunk_size], f"{current_day}{i}")
            person["guesses"].insert(0, guess)
        
        # Remove those guesses from the summary
        for guess in summary:
            summary.remove(guess)
    
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

    # Start the server
    port = config.get("port", 3465)
    print(f"Starting server on http://127.0.0.1:{port}")
    print(get_person(current_day)["name"])
    serve(app, host="0.0.0.0", port=port, threads=8)
