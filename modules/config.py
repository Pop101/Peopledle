import yaml
from io import open

cfg = None
def __load_cfg():
    with open("config.yml", "r", encoding="utf-8") as f:
        raw_cfg = yaml.safe_load(f)
    
    return {
        k.lower().replace(" ", "_"): v
        for k, v in raw_cfg.items()
    }

def get_cfg():
    global cfg
    if not cfg:
        cfg = __load_cfg()
    return cfg

def get(key:str, default=None):
    key = key.lower().replace(" ", "_")
    if key not in get_cfg():
        return default
    return get_cfg()[key]