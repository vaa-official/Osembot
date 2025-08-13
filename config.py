import os
class Config:
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'your_strong_secret_key_here')
    DEBUG = True
    PORT = 5000
    CACHE_TTL = 300 
    NLTK_DATA_PATH = os.path.join(os.path.dirname(__file__), 'nltk_data')
    INTENTS_FILE = "intents.json"