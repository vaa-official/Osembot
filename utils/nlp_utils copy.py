# This is the nlp code which only provide  the english response
import nltk
import re
import string
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
import os
import json
from config import Config

nltk.data.path.append(Config.NLTK_DATA_PATH)
stop_words = set(stopwords.words('english'))

def preprocess_text(text):
    text = text.lower().translate(str.maketrans('', '', string.punctuation))
    tokens = [word for word in text.split() if word not in stop_words]
    return ' '.join(tokens)

def normalize(text):
    return re.sub(r'\W+', '', text.lower())

def load_intents():
    try:
        with open(Config.INTENTS_FILE, "r", encoding='utf-8') as file:
            return json.load(file)
    except Exception:
        return []

def initialize_nlp():
    intents_data = load_intents()
    corpus = []
    tags = []
    responses = {}

    for item in intents_data:
        if all(k in item for k in ("intent", "patterns", "responses")):
            intent = item["intent"]
            processed_patterns = [preprocess_text(p) for p in item["patterns"]]
            corpus.extend(processed_patterns)
            tags.extend([intent] * len(processed_patterns))
            responses[intent] = item["responses"]
    
    vectorizer = TfidfVectorizer()
    if corpus:
        X = vectorizer.fit_transform(corpus)
    else:
        X = None
    
    return vectorizer, X, tags, responses