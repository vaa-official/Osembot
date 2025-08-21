import nltk
import re
import string
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
import json
from config import Config
from googletrans import Translator

# Initialize NLTK
try:
    stop_words = set(stopwords.words('english'))
except LookupError:
    nltk.download('stopwords')
    stop_words = set(stopwords.words('english'))

# Initialize translator
translator = Translator()

def preprocess_text(text):
    text = text.lower().translate(str.maketrans('', '', string.punctuation))
    tokens = [word for word in text.split( ) if word not in stop_words]
    return ' '.join(tokens)

def normalize(text):
    return re.sub(r'\W+', '', text.lower())

def load_intents():
    try:
        with open(Config.INTENTS_FILE, "r", encoding='utf-8') as file:
            return json.load(file)
    except Exception:
        return []

def translate_to_hindi(text):
    """Translate English text to Hindi."""
    try:
        translated = translator.translate(text, src='en', dest='hi')
        return translated.text
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # fallback

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

            # Combine English + Hindi in the same response but on separate lines
            combined_responses = []
            for resp in item["responses"]:
                hindi = translate_to_hindi(resp)
                combined_responses.append(f"{resp}\n{hindi}")
            responses[intent] = combined_responses
    
    vectorizer = TfidfVectorizer()
    if corpus:
        X = vectorizer.fit_transform(corpus)
    else:
        X = None
    
    return vectorizer, X, tags, responses
