import hashlib

def hash(x):
    return int(hashlib.md5(repr(x).encode("utf-8")).hexdigest(), 16)

seed = hash(0)

def reseed():
    global seed
    seed = hash(seed)

def set_seed(x:int):
    global seed
    seed = hash(x)

def choice(x, _seed:int = None):
    # Deterministic choice
    if _seed is None:
        _seed = seed
    return x[hash(_seed) % len(x)]

def random():
    # Deterministic random, 0-1
    # Does not reset seed
    return hash(seed) / 2**128

def randint(a:int, b:int):
    # Deterministic random, a-b
    # Does not reset seed
    return a + hash(seed) % (b - a)

if __name__ == "__main__":
    print("Hash Correctness Test:", hash(0) == 276215275525073243129443018166533317850)
    print("Rand Correctness Test:", random() == 0.08723842685046378)
    print("Randint Correctness Test:", randint(0, 10) == 4)
    