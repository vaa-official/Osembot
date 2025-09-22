import time
import threading
from config import Config

api_cache = {}
cache_lock = threading.Lock()

def cache_data(key, data):
    with cache_lock:
        api_cache[key] = {
            'data': data,
            'timestamp': time.time()
        }

def get_cached_data(key):
    current_time = time.time()
    with cache_lock:
        if key in api_cache:
            cache_entry = api_cache[key]
            if current_time - cache_entry['timestamp'] < Config.CACHE_TTL:
                return cache_entry['data']
    return None

def clear_cache():
    with cache_lock:
        api_cache.clear()