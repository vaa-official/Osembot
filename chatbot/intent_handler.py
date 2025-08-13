import re
import random
import logging
import requests
from flask import Flask, jsonify, session
from sklearn.metrics.pairwise import cosine_similarity
import os


from utils.nlp_utils import preprocess_text, normalize
from utils.data_fetcher import (
    fetch_business_data, 
    fetch_expert_data,
    fetch_services,
    fetch_market_linkage,
    fetch_events
    
)

logger = logging.getLogger(__name__)

vectorizer, X, tags, responses = None, None, None, None

def initialize_chatbot():
    global vectorizer, X, tags, responses
    from utils.nlp_utils import initialize_nlp
    vectorizer, X, tags, responses = initialize_nlp()

valid_cities = ["agra", "kanpur", "lucknow"]

def extract_city(text):
    words = preprocess_text(text).split()
    for word in words:
        if word in valid_cities:
            return word
    return None

def is_city_business_query(text):
    text = text.lower()
    keywords = ["how many business", "business in", "number of business"]
    return any(k in text for k in keywords)
def load_chat_history():
    """Loads chat history from the session."""
    return session.get('chat_history', [])

def save_chat_history(chat_history):
    """Saves chat history to the session."""
    session['chat_history'] = chat_history

def find_experts_in_district(query_lower, expert_data):
    """Finds experts in a specified district from the expert data."""
    match = re.search(r'(?:who is the expert in|list of expert in)\s+([a-z\s]+)', query_lower)
    if match:
        district_queried = match.group(1).strip()
        experts_in_district = []
        for expert in expert_data:
            if expert.get('district') and normalize(expert['district']) == normalize(district_queried):
                experts_in_district.append(expert.get('name', 'N/A'))
        if experts_in_district:
            return f"The expert(s) in {district_queried.title()} is/are: {', '.join(experts_in_district)}."
        else:
            return f"No expert found in {district_queried.title()}."
    else:
        return "Please specify the district (e.g., 'who is the expert in Lucknow')."

def handle_query(query, business_data, expert_data, service_data, market_linkage_data, event_data):
    """
    Processes the user's query and generates a response based on available data.
    Prioritizes specific API-driven rules, then hardcoded intent rules, then a general fallback.
    """
    query_lower = query.lower().strip()

   
    if query_lower in ['hi', 'hello', 'hlo']:
        return "Hello! 👋 How can I assist you today?"
    elif query_lower in ['how are you', 'how are you doing']:
        return "I'm just a chatbot, but I'm doing great! 😊 How can I help you?"
    elif "where are you located" in query_lower or "your location" in query_lower:
        return "I am an AI assistant and do not have a physical location."

    
    match = re.search(r"how many expert[s]? in (\w+)", query_lower)
    if match:
        location = match.group(1)
        count = sum(1 for item in expert_data if item.get("district", "").lower() == location.lower())
        return f"There are {count} experts in {location.title()}."

    match = re.search(r"designation of ([a-zA-Z\s]+)", query_lower)
    if match:
        name = match.group(1).strip().lower()
        for item in expert_data:
            if normalize(item.get("name", "")) == normalize(name):
                return f"The designation of {name.title()} is {item.get('designation', 'Not available')}."
        return f"Expert named {name.title()} not found."

    # General contact/email/URN/ID queries for businesses and experts
    for label, key_business, key_expert in [
        ("contact number", "business_contact", "mobile"),
        ("email", "business_email", "email"),
        ("urn", "business_urn", None), 
        ("id", "id", "id") 
    ]:
        if label in query_lower and 'of' in query_lower:
            name_part = query_lower.split('of', 1)[1].strip().lower()
            for d in business_data:
                if normalize(name_part) in normalize(d.get("business_name", "")):
                    return f"{label.title()} of {d['business_name']}: {d.get(key_business, 'Not available')}"
            if key_expert:
                for e in expert_data:
                    if normalize(name_part) in normalize(e.get("name", "")):
                        return f"{label.title()} of {e['name']}: {e.get(key_expert, 'Not available')}"
            return f"Name '{name_part.title()}' not found in businesses or experts."

    # Business Listing and Counts
    if 'list' in query_lower and 'business' in query_lower:
        try:
            if 'lucknow' in query_lower and 'female' in query_lower:
                filtered_businesses = [
                    f"<li>{d['business_name']} - {d['owner_name']}</li>"
                    for d in business_data
                    if 'lucknow' in d.get('business_district', '').lower() and
                    'female' in d.get('owner_gender', '').lower()
                ]
                if filtered_businesses:
                    return "<p>Female-owned businesses in Lucknow:</p><ul>" + "".join(filtered_businesses) + "</ul>"
                return "No female-owned businesses found in Lucknow."

            elif 'enterprises' in query_lower:
                filtered_businesses = [
                    f"<li>{d['business_name']} - {d['owner_name']}</li>"
                    for d in business_data
                    if 'enterprises' in d.get('business_name', '').lower()
                ]
                if filtered_businesses:
                    return "<p>Businesses with 'enterprises' in the name:</p><ul>" + "".join(filtered_businesses) + "</ul>"
                return "No enterprises found."

            else:
                if business_data:
                    all_businesses = [
                        f"<li>{d['business_name']}</li>" for d in business_data
                    ]
                    return "<p>All businesses:</p><ul>" + "".join(all_businesses) + "</ul>"
                return "No businesses found."

        except Exception as e:
            logger.error(f"An error occurred while listing businesses: {e}", exc_info=True)
            return f"An error occurred while listing businesses: {str(e)}"

    # Female and Male owner queries (general, not specific to business listing)
    if 'business' not in query_lower:
     if 'female' in query_lower:
        female_owners = [
            f"<li>{d.get('business_name', 'N/A')} - {d.get('owner_name', 'N/A')}</li>"
            for d in business_data
            if d.get('owner_gender', '').strip().lower() == 'female'
        ]
        return (
            "<p>Here is the list of all <strong>female</strong> business owners:</p><ul>"
            + "".join(female_owners) +
            "</ul>" if female_owners else "No female business owners found."
        )

    elif 'male' in query_lower:
        male_owners = [
            f"<li>{d.get('business_name', 'N/A')} - {d.get('owner_name', 'N/A')}</li>"
            for d in business_data
            if d.get('owner_gender', '').strip().lower() == 'male'
        ]
        return (
            "<p>Here is the list of all <strong>male</strong> business owners:</p><ul>"
            + "".join(male_owners) +
            "</ul>" if male_owners else "No male business owners found."
        )

    if 'owner name' in query_lower and 'of' in query_lower:
        business = query_lower.split('of', 1)[1].strip()
        for d in business_data:
            if normalize(business) in normalize(d.get('business_name', '')):
                return f"Owner name of {d['business_name']}: {d.get('owner_name', 'Not available')}"
        return "Business not found."

    elif 'gender' in query_lower and 'of' in query_lower:
        business = query_lower.split('of', 1)[1].strip()
        for d in business_data:
            if normalize(business) in normalize(d.get('business_name', '')):
                return f"Gender of owner: {d.get('owner_gender', 'Not specified')}"
        return "Business not found."

    elif 'how many business in' in query_lower:
        city_match = re.search(r"how many business in (.+)", query_lower)
        if city_match:
            city = city_match.group(1).strip()
            count = sum(1 for d in business_data if city.lower() in d.get('business_district', '').lower())
            return f"There are {count} businesses in {city.title()}."
        return "Please specify the city, e.g., 'how many business in Lucknow'."

    elif "how many business" in query_lower or "total business" in query_lower:
        return f"There are {len(business_data)} businesses in the list."

    match = re.search(r"name the business in ([a-zA-Z\s]+)", query_lower)
    if match:
        district_name = match.group(1).strip()
        found_businesses = [
            f"- {d['business_name']}"
            for d in business_data
            if normalize(d.get('business_district', '')) == normalize(district_name)
        ]
        if found_businesses:
            return f"Here are the businesses in {district_name.title()}:<br>" + "<br>".join(found_businesses)
        else:
            return f"No businesses found in {district_name.title()}."

    if "who is the owner of" in query_lower:
        match = re.search(r"who is the owner of ([a-zA-Z\s]+)", query_lower)
        if match:
            business_name = match.group(1).strip()
            for business in business_data:
                if normalize(business.get('business_name', '')) == normalize(business_name):
                    return f"The owner of {business['business_name']} is {business.get('owner_name', 'Not Available')}."
            return f"Business '{business_name.title()}' not found."

    if "what is the designation of the owner of" in query_lower:
        match = re.search(r"what is the designation of the owner of ([a-zA-Z\s]+)", query_lower)
        if match:
            business_name = match.group(1).strip()
            for business in business_data:
                if normalize(business.get('business_name', '')) == normalize(business_name):
                    return f"The designation of the owner of {business['business_name']} is {business.get('owner_designation', 'Not Available')}."
            return f"Business '{business_name.title()}' not found."

    if "what is the gender of the owner of" in query_lower:
        match = re.search(r"what is the gender of the owner of ([a-zA-Z\s]+)", query_lower)
        if match:
            business_name = match.group(1).strip()
            for business in business_data:
                if normalize(business.get('business_name', '')) == normalize(business_name):
                    return f"The gender of the owner of {business['business_name']} is {business.get('owner_gender', 'Not Available')}."
            return f"Business '{business_name.title()}' not found."

    if "what is the category of the owner of" in query_lower:
        match = re.search(r"what is the category of the owner of ([a-zA-Z\s]+)", query_lower)
        if match:
            business_name = match.group(1).strip()
            for business in business_data:
                if normalize(business.get('business_name', '')) == normalize(business_name):
                    return f"The category of the owner of {business['business_name']} is {business.get('owner_category', 'Not Available')}."
            return f"Business '{business_name.title()}' not found."

    if "what type of business is" in query_lower:
        match = re.search(r"what type of business is ([a-zA-Z\s]+)", query_lower)
        if match:
            business_name = match.group(1).strip()
            for business in business_data:
                if normalize(business.get('business_name', '')) == normalize(business_name):
                    return f"{business['business_name']} is a {business.get('business_industry', 'Not Available')} business."
            return f"Business '{business_name.title()}' not found."

    if "what is the urn number of" in query_lower:
        match = re.search(r"what is the urn number of ([a-zA-Z\s]+)", query_lower)
        if match:
            business_name = match.group(1).strip()
            for business in business_data:
                if normalize(business.get('business_name', '')) == normalize(business_name):
                    return f"The URN number of {business['business_name']} is {business.get('business_urn', 'Not Available')}."
            return f"Business '{business_name.title()}' not found."

    if "what is the contact number of" in query_lower:
        match = re.search(r"what is the contact number of ([a-zA-Z\s]+)", query_lower)
        if match:
            business_name = match.group(1).strip()
            for business in business_data:
                if normalize(business.get('business_name', '')) == normalize(business_name):
                    return f"The contact number of {business['business_name']} is {business.get('business_contact', 'Not Available')}."
            return f"Business '{business_name.title()}' not found."

    if "what is the email id of" in query_lower:
        match = re.search(r"what is the email id of ([a-zA-Z\s]+)", query_lower)
        if match:
            business_name = match.group(1).strip()
            for business in business_data:
                if normalize(business.get('business_name', '')) == normalize(business_name):
                    return f"The email ID of {business['business_name']} is {business.get('business_email', 'Not Available')}."
            return f"Business '{business_name.title()}' not found."

    if "what is the industry type of" in query_lower:
        match = re.search(r"what is the industry type of ([a-zA-Z\s]+)", query_lower)
        if match:
            business_name = match.group(1).strip()
            for business in business_data:
                if normalize(business.get('business_name', '')) == normalize(business_name):
                    return f"The industry type of {business['business_name']} is {business.get('business_industry', 'Not Available')}."
            return f"Business '{business_name.title()}' not found."

    if "what does" in query_lower and "manufacture" in query_lower:
        match = re.search(r"what does ([a-zA-Z\s]+) manufacture", query_lower)
        if match:
            business_name = match.group(1).strip()
            for business in business_data:
                if normalize(business.get('business_name', '')) == normalize(business_name):
                    return f"{business['business_name']} manufactures {business.get('business_activity', 'Not Available')}."
            return f"Business '{business_name.title()}' not found."

    if "what is the pin code of" in query_lower:
        match = re.search(r"what is the pin code of ([a-zA-Z\s]+)", query_lower)
        if match:
            business_name = match.group(1).strip()
            for business in business_data:
                if normalize(business.get('business_name', '')) == normalize(business_name):
                    return f"The pin code of {business['business_name']} is {business.get('business_pincode', 'Not Available')}."
            return f"Business '{business_name.title()}' not found."

    if "who is the finance expert" in query_lower:
        for expert in expert_data:
            if normalize(expert.get('designation', '')) == normalize("Finance Expert"):
                return f"The finance expert is {expert.get('name', 'N/A')}."
        return "No finance expert found."

    if "what is the email of" in query_lower:
        match = re.search(r"what is the email of ([a-zA-Z\s]+)", query_lower)
        if match:
            expert_name = match.group(1).strip()
            for expert in expert_data:
                if normalize(expert.get('name', '')) == normalize(expert_name):
                    return f"The email of {expert.get('name', 'N/A')} is {expert.get('email', 'N/A')}."
            return f"Expert named '{expert_name.title()}' not found."

    if "what is the contact number of" in query_lower:
        match = re.search(r"what is the contact number of ([a-zA-Z\s]+)", query_lower)
        if match:
            expert_name = match.group(1).strip()
            for expert in expert_data:
                if normalize(expert.get('name', '')) == normalize(expert_name):
                    return f"The contact number of {expert.get('name', 'N/A')} is {expert.get('mobile', 'N/A')}."
            return f"Contact number for expert named '{expert_name.title()}' not found."

    if "what is the designation of" in query_lower:
        match = re.search(r"what is the designation of ([a-zA-Z\s]+)", query_lower)
        if match:
            expert_name = match.group(1).strip()
            for expert in expert_data:
                if normalize(expert.get('name', '')) == normalize(expert_name):
                    return f"{expert.get('name', 'N/A')} is a {expert.get('designation', 'N/A')}."
            return f"Expert named '{expert_name.title()}' not found."

    if "who is the expert in" in query_lower or "list of expert in" in query_lower:
        return find_experts_in_district(query_lower, expert_data)

    if "what is the address of the finance expert" in query_lower:
        for expert in expert_data:
            if normalize(expert.get('designation', '')) == normalize("Finance Expert"):
                return f"The address of the finance expert ({expert.get('name', 'N/A')}) is in {expert.get('district', 'N/A')}, {expert.get('state', 'N/A')}."
        return "No address found for the finance expert."

    # Services
    if re.search(r"(how many|number of)\s+services.*(osem)?", query_lower) or \
       "what services are available" in query_lower or \
       "osem services" in query_lower or \
       "what services do you offer" in query_lower:
        try:
            services = service_data
            if not services:
                return "Sorry, no services found at the moment."

            response_lines = [f"<p>OSEM provides {len(services)} services. Here are the details:</p><ul>"]

            for service in services:
                name = service.get("service") or service.get("service_name") or service.get("name") or "Unnamed Service"
                category = service.get("category", "N/A")
                price = service.get("price", "N/A")
                days = service.get("days", "N/A")
                response_lines.append(f"<li>🔹 {name} (Category: {category}, Price: ₹{price}, Completion Time: {days} days)</li>")

            response_lines.append("</ul>")
            return "".join(response_lines)

        except Exception as e:
            logger.error(f"An error occurred while listing services: {e}", exc_info=True)
            return f"An error occurred: {str(e)}"

    # Market Linkage
    if "market linkage" in query_lower:
        ml_data = market_linkage_data
        if not ml_data:
            return "No market linkage programs found at the moment."
        if query_lower == "market linkage" or query_lower == "what market linkages are available":
            response_lines = ["Here are the market linkage programs available:"]
            for item in ml_data:
                name = item.get("ml_name") or item.get("name") or "Unnamed Program"
                description = item.get("ml_desc") or item.get("description") or "No description available."
                response_lines.append(f"🔗 {name}: {description}")
            if len(response_lines) > 1:
                return "<br>".join(response_lines)
            return "No market linkage programs found."

    # Events
    if "events" in query_lower or "upcoming programs" in query_lower:
        try:
            events = event_data
            if not events:
                return "No upcoming events found at the moment."

            response_lines = ["<p>Here are the upcoming events:</p><ul>"]

            for event in events:
                name = event.get("event_name") or event.get("name") or "Unnamed Event"
                date = event.get("event_date") or event.get("date") or "Date not specified"
                location = event.get("event_location") or event.get("location") or "Location not specified"
                response_lines.append(f"<li>📅 {name} (Date: {date}, Location: {location})</li>")

            response_lines.append("</ul>")
            return "".join(response_lines)

        except Exception as e:
            logger.error(f"An error occurred while fetching events: {e}", exc_info=True)
            return f"An error occurred while fetching events: {str(e)}"

    # --- Rule-based Intent Matching (Lower Priority Fallback) ---
    processed_input = preprocess_text(query)
    if not processed_input:
        return random.choice(responses.get("fallback", ["I'm not sure I understood that. Can you try rephrasing?"]))

    if is_city_business_query(query):
        city = extract_city(query)
        if city:
            count = sum(1 for d in business_data if city.lower() in d.get('business_district', '').lower())
            return f"There are {count} listed businesses in {city.capitalize()}."
        else:
            return "Sorry, this city is not listed in my business data. Please try another city."

    if X is not None:
        user_vec = vectorizer.transform([processed_input])
        sim_scores = cosine_similarity(user_vec, X)
        best_match_index = sim_scores.argmax()
        confidence = sim_scores[0, best_match_index]

        if confidence > 0.3: # Confidence threshold for intent matching
            best_intent = tags[best_match_index]
            return random.choice(responses.get(best_intent, ["Sorry, I can't answer that right now."]))

    return random.choice(responses.get("fallback", [
        "I'm not sure I understood that. Can you try rephrasing or asking something else?",
        "My apologies, I don't have information on that. Can I help with something else?",
        "I'm still learning! Could you please ask in a different way?"
    ]))


    # Fetch all required data (cached)
    business_data = fetch_business_data()
    expert_data = fetch_expert_data()
    service_data = fetch_services()
    market_linkage_data = fetch_market_linkage()
    event_data = fetch_events()