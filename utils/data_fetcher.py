import requests
import json
import logging
from .cache_manager import cache_data, get_cached_data

logger = logging.getLogger(__name__)

def fetch_data_from_api(action, default_return_data=None):
    if default_return_data is None:
        default_return_data = []
    
   
    cached = get_cached_data(action)
    if cached:
        return cached

    url = "https://msmeosem.in/apis/root/common.php"
    headers = {
        "Accept": "*/*",
        "User-Agent": "MSME_Chatbot/1.0",
        "Content-Type": "application/json"
    }
    payload = {"action": action}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        json_data = response.json()
        
        if isinstance(json_data, dict) and 'data' in json_data:
            result = json_data['data']
        elif isinstance(json_data, list):
            result = json_data
        else:
            result = default_return_data
    except Exception as e:
        logger.error(f"Error fetching {action} data: {str(e)}")
        result = default_return_data
    
    cache_data(action, result)
    return result

def fetch_business_data():
    return fetch_data_from_api("business")

def fetch_expert_data():
    return fetch_data_from_api("experts")

def fetch_services():
    return fetch_data_from_api("services")

def fetch_market_linkage():
    return fetch_data_from_api("marketLinkage")

def fetch_events():
    return fetch_data_from_api("events")