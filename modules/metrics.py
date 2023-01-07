import sqlite3
from . import config

def __ensure_db_exists():
    conn = sqlite3.connect(config.get("database_location", "./metrics.db"))
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS guesses (uuid VARCHAR(32), day INTEGER, guesses INTEGER, correct INTEGER DEFAULT 0)")
    c.close()
    conn.commit()
    return conn

def get_average(day:int):
    conn = __ensure_db_exists()
    c = conn.cursor()
    c.execute("SELECT AVG(guesses) FROM guesses WHERE day=?", (day,))
    
    avg = c.fetchone()[0]
    if not avg: avg = 0
    
    conn.close()
    return avg

def record_guess(uuid:str, day:int, guesses:int, correct:bool = False):
    conn = __ensure_db_exists()
    c = conn.cursor()
    if len(uuid) > 32:
        raise ValueError("UUID must be 32 characters or less")
    c.execute("INSERT INTO guesses VALUES (?, ?, ?, ?)", (uuid, day, guesses, int(correct)))
    conn.commit()
    conn.close()