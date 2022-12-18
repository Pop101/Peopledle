import os
import json

from .filedb_exceptions import validate_name, is_name_valid
from .simplecache import FixedSizeDict


class MongrelDB:
    """A simple database that stores data in JSON files"""

    def __init__(self, path: str, cache_size: int = 1000 * 1024) -> None:
        """Initializes the database

        Args:
            path (str): The path to the database folder
            cache_size (int, optional): The maximum cache size to use. Set to -1 to infinitely cache. Defaults to 1000KB.
        """

        if os.path.exists(path) == False:
            os.makedirs(path)

        self.path = path
        self.cache = FixedSizeDict(cache_size)

    def __getitem__(self, name):
        validate_name(name)
        if name in self.cache:
            return self.cache[name]

        dbpath = os.path.join(self.path, f"{name}.json")
        if os.path.exists(dbpath):
            with open(dbpath, "r") as file:
                return json.load(file)
        else:
            return None

    def __setitem__(self, name, val):
        validate_name(name)
        self.cache[name] = val

        val = json.dumps(val)
        name = f"{name}.json"
        with open(os.path.join(self.path, name), "w") as file:
            file.write(val)

    def __delitem__(self, name):
        if not is_name_valid(name):
            return
        del self.cache[name]

        dbpath = os.path.join(self.path, f"{name}.json")
        if os.path.exists(dbpath) and os.path.isfile(dbpath):
            os.remove(dbpath)

    def __contains__(self, name):
        if not is_name_valid(name):
            return False

        dbpath = os.path.join(self.path, f"{name}.json")
        return os.path.exists(dbpath) and os.path.isfile(dbpath)

    def __iter__(self):
        for file in os.listdir(self.path):
            if file.endswith(".json"):
                yield file[:-5]

    def __len__(self):
        return len(list(iter(self)))


if __name__ == "__main__":
    import shutil

    db = Database("./TESTDB")
    db["abcde"] = [{"start": 123, "end": 456}, {}]
    print(db["abcde"])
    print("abcde" in db)
    print("abcdef" in db)

    shutil.rmtree("./TESTDB")
