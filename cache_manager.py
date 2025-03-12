import os
import hashlib
import json
import time
from contextlib import suppress

CACHE_DIR = "./cache"
CACHE_EXPIRATION = 60 * 60 * 24 * 30

os.makedirs(CACHE_DIR, exist_ok=True)


def _get_cache_filename(lat, lon):
    key = f"{lat},{lon}".encode()
    return os.path.join(CACHE_DIR, hashlib.md5(key).hexdigest() + ".cache")


def save_to_cache(lat, lon, content):
    try:
        with open(_get_cache_filename(lat, lon), "w", encoding="utf-8") as f:
            json.dump({"address": content, "timestamp": time.time()}, f)
    except Exception as e:
        print(f"Cache writing error: {e}")


def load_from_cache(lat, lon):
    cache_file = _get_cache_filename(lat, lon)
    if os.path.isfile(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if time.time() - data["timestamp"] < CACHE_EXPIRATION:
                    print(f"Use cache for {lat}, {lon}")
                    return data["address"]
        except Exception as e:
            print(f"Cache reading error: {e}")
        with suppress(FileNotFoundError):
            os.remove(cache_file)
    return None


def clear_cache():
    with suppress(FileNotFoundError):
        for entry in os.scandir(CACHE_DIR):
            if entry.is_file():
                os.remove(entry.path)
