from flask import Flask, jsonify, request, session, render_template, Response, stream_with_context
import logging
import os
import time

from .intent_handler import handle_query, initialize_chatbot
from utils.data_fetcher import (
    fetch_business_data,
    fetch_expert_data,
    fetch_services,
    fetch_market_linkage,
    fetch_events,
)
from utils.cache_manager import clear_cache, api_cache, cache_lock
from utils.nlp_utils import normalize

app = Flask(__name__)
app.secret_key = 'your_strong_secret_key_here'

# Initialize chatbot on first use
initialize_chatbot()

# --- Chat History Functions ---
def load_chat_history():
    return session.get('chat_history', [])

def save_chat_history(chat_history):
    session['chat_history'] = chat_history



@app.route("/api/business_list", methods=["GET"])
def get_business_list():
    business_data = fetch_business_data()
    districts = {business.get('business_district', '').strip().title() for business in business_data if business.get('business_district')}
    return jsonify({"districts": sorted(districts)})

@app.route("/api/business_in_district", methods=["GET"])
def get_business_in_district():
    district = request.args.get('district', '').strip()
    if not district:
        return jsonify({"error": "District parameter is required"}), 400

    business_data = fetch_business_data()
    business_in_district = [
        {
            "name": business.get('business_name', 'N/A'),
            "email": business.get('business_email', 'N/A'),
            "mobile": business.get('business_contact', 'N/A'),
            "address": business.get('business_address', 'N/A')
        }
        for business in business_data
        if normalize(business.get('business_district', '').strip()) == normalize(district)
    ]

    return jsonify({
        "district": district.title(),
        "business": business_in_district
    })

@app.route("/api/expert_list", methods=["GET"])
def get_expert_list():
    expert_data = fetch_expert_data()
    districts = {expert.get('district', '').strip().title() for expert in expert_data if expert.get('district')}
    return jsonify({"districts": sorted(districts)})

@app.route("/api/experts_in_district", methods=["GET"])
def get_experts_in_district():
    district = request.args.get('district', '').strip()
    if not district:
        return jsonify({"error": "District parameter is required"}), 400

    expert_data = fetch_expert_data()
    experts_in_district = [
        {
            "name": expert.get('name', 'N/A'),
            "designation": expert.get('designation', 'N/A'),
            "email": expert.get('email', 'N/A'),
            "mobile": expert.get('mobile', 'N/A')
        }
        for expert in expert_data
        if normalize(expert.get('district', '').strip()) == normalize(district)
    ]

    return jsonify({
        "district": district.title(),
        "experts": experts_in_district
    })

@app.route("/api/expert_designations", methods=["GET"])
def get_expert_designations():
    expert_data = fetch_expert_data()
    designations = {expert.get('designation', '').strip().title() for expert in expert_data if expert.get('designation')}
    return jsonify({"designations": sorted(designations)})

@app.route("/api/experts_by_designation", methods=["GET"])
def get_experts_by_designation():
    designation = request.args.get('designation', '').strip()
    if not designation:
        return jsonify({"error": "Designation parameter is required"}), 400

    expert_data = fetch_expert_data()
    experts_with_designation = [
        {
            "name": expert.get('name', 'N/A'),
            "district": expert.get('district', 'N/A'),
            "email": expert.get('email', 'N/A'),
            "mobile": expert.get('mobile', 'N/A')
        }
        for expert in expert_data
        if normalize(expert.get('designation', '').strip()) == normalize(designation)
    ]

    return jsonify({
        "designation": designation.title(),
        "experts": experts_with_designation
    })

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/chat", methods=["GET", "POST"])
def chat():
    user_message = ""
    if request.method == "GET":
        user_message = request.args.get('message', '').strip()
        if not user_message:
            return jsonify({"response": "Please provide a message parameter in the URL"}), 400
    else:
        if request.is_json:
            user_message = request.json.get('message', '').strip()
        else:
            user_message = request.form.get('message', '').strip()

        if not user_message:
            return jsonify({'response': "Please enter a message in the request body."}), 400

    # 🔧 Fetch required data
    business_data = fetch_business_data()
    expert_data = fetch_expert_data()
    service_data = fetch_services()
    market_linkage_data = fetch_market_linkage()
    event_data = fetch_events()

    # ✅ Call handle_query with all arguments
    response_text = handle_query(
        user_message,
        business_data,
        expert_data,
        service_data,
        market_linkage_data,
        event_data
    )

    # Save chat history
    chat_history = load_chat_history()
    chat_history.append({"user": user_message, "bot": response_text})
    save_chat_history(chat_history)

    if request.method == "GET":
        return jsonify({"response": response_text})
    else:
        def generate():
            words = response_text.replace('<br>', ' ').split()
            for word in words:
                yield word + " "
                time.sleep(0.05)
            yield "\n"

        return Response(stream_with_context(generate()), mimetype='text/plain')

@app.route("/api/clear_chat", methods=["POST"])
def clear_chat():
    session.pop('chat_history', None)
    return jsonify({"response": "Chat history cleared!"})

@app.route("/api/clear_cache", methods=["POST"])
def clear_cache_route():
    clear_cache()
    logging.info("API cache cleared")
    return jsonify({"status": "success", "message": "Cache cleared"})

@app.route("/check-eligibility", methods=["POST"])
def check_eligibility():
    data = request.get_json()
    age = int(data.get("age", 0))
    
    if 21 <= age <= 40:
        return jsonify({
            "message": " OK, you are eligible for CM Yuva.",
            "ask_certificate": True
        })
    else:
        return jsonify({
            "message": " Sorry, this loan is only for people between 21 and 40 years old.",
            "ask_certificate": False
        })

@app.route("/check-certificate", methods=["POST"])
def check_certificate():
    data = request.get_json()
    skill = data.get("skill", "").lower()
    
    if skill == "yes":
        return jsonify({
            "message": " OK, you are eligible for the loan.",
            "ask_about_loan": True
        })
    else:
        return jsonify({
            "message": " Sorry, you need a skill certificate to apply for the loan.",
            "ask_about_loan": False
        })

if __name__ == '__main__':
    if not os.path.exists('templates'):
        os.makedirs('templates')

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Starting Flask application with caching...")

    app.run(debug=True, port=5000, use_reloader=False)
