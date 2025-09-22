import nltk
import re
import string
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
import json
from config import Config
from deep_translator import GoogleTranslator

# Initialize NLTK
nltk.data.path.append(Config.NLTK_DATA_PATH)
stop_words = set(stopwords.words('english'))

# Translator (Google via deep-translator)
translator = GoogleTranslator(source='en', target='hi')

def preprocess_text(text):
    """Lowercase, remove punctuation & stopwords."""
    text = text.lower().translate(str.maketrans('', '', string.punctuation))
    tokens = [word for word in text.split() if word not in stop_words]
    return ' '.join(tokens)

def normalize(text):
    """Normalize text for comparison."""
    return re.sub(r'\W+', '', text.lower())

def load_intents():
    """Load intents from JSON file."""
    try:
        with open(Config.INTENTS_FILE, "r", encoding='utf-8') as file:
            return json.load(file)
    except Exception:
        return []

def translate_to_hindi(text):
    """Translate English text to Hindi."""
    try:
        translated = translator.translate(text)
        return translated
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # fallback

def initialize_nlp():
    """Prepare vectorizer, training corpus, tags, and responses."""
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
