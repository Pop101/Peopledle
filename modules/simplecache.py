import sys
from collections import OrderedDict


# Cache annotation and cache object that uses a dict to map inputs to outputs
# Individual objects can be flagged for deletion
# If the cache exceeds a certain size, the oldest objects are deleted

EMPTY_DICT_SIZE = sys.getsizeof(OrderedDict())
KB = 1024
MB = 1048576


class FixedSizeDict:
    def __init__(self, size_limit: int = 1000 * 1024, **kwargs) -> None:
        self.size_limit = int(size_limit)
        self.dict = OrderedDict()

        # Add any kwargs to the dict
        for key, val in kwargs.items():
            self[key] = val
        while sys.getsizeof(self.dict) > self.size_limit - EMPTY_DICT_SIZE and self.size_limit >= 0 and len(self.dict) > 0:
            self.dict.popitem(last=False)

    def clear(self) -> None:
        self.dict.clear()

    def copy(self) -> "FixedSizeDict":
        return FixedSizeDict(self.size_limit, **self.dict)

    def update_size_limit(self, size_limit: int):
        self.size_limit = size_limit
        while sys.getsizeof(self.dict) > self.size_limit - EMPTY_DICT_SIZE and size_limit >= 0 and len(self.dict) > 0:
            self.dict.popitem(last=False)

    def __contains__(self, key):
        return key in self.dict

    def __getitem__(self, key):
        if key not in self.dict:
            return None
        self.dict.move_to_end(key)
        return self.dict[key]

    def __setitem__(self, key, val):
        self.dict[key] = val
        self.dict.move_to_end(key)
        while (
            sys.getsizeof(self.dict) > self.size_limit - EMPTY_DICT_SIZE and self.size_limit >= 0 and len(self.dict) > 0
        ):
            self.dict.popitem(last=False)

    def __delitem__(self, key):
        if key not in self.dict:
            return None
        del self.dict[key]

    def __len__(self):
        return len(self.dict)

    def __repr__(self):
        return repr(f"<FixedSizeDict size_limit={self.size_limit} dict={self.dict}>")

    def __str__(self):
        return str(self.dict)

    def __iter__(self):
        return iter(self.dict)

    def __next__(self):
        return next(self.dict)

def hash_noerr(obj):
    if isinstance(obj, dict): return hash(tuple(obj.items()))
    try: return hash(obj)
    except TypeError: return hash(obj.__dict__.items())
    
# Worse than lru cache for several reasons.
# most of all, hash algo is ran multiple times
# https://github.com/python/cpython/blob/main/Lib/functools.py
def cache(size_limit: int = 256 * KB):
    def decorator(func):
        cache = FixedSizeDict(size_limit)

        def wrapper(*args, **kwargs):
            # Generate unique key for the function call
            # Like LRUCache it fails when args are in a different order
            key = tuple()
            for arg in args:
                key += (hash_noerr(arg),)
            if kwargs:
                key += (object(),)
            for kwarg_idx, kwarg_val in kwargs.items():
                key += (hash_noerr(kwarg_idx), hash_noerr(kwarg_val))
            
            # Check table for key, run if DNE
            if key in cache:
                return cache[key]
            else:
                value = func(*args, **kwargs)
                cache[key] = value
                return value

        return wrapper

    return decorator