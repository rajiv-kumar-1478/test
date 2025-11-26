import requests
import json
import os

# API endpoints
SEARCH_URL = "https://test-hn4h.onrender.com/search_users?key={}"
RESULT_URL = "https://api.buddy4study.com/api/v1.0/ssms/scholarship/hdfc-bank-parivartan-s-ecss-programme-for-undergraduate-courses-merit-cum-need-based-2024-25/result/filter"

ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzY29wZSI6WyJyZWFkIiwid3JpdGUiLCJ0cnVzdCJdLCJleHAiOjE3OTAxNTcyMjgsImF1dGhvcml0aWVzIjpbIlVTRVIiXSwianRpIjoiMzc0NTE5NTUtYTA5OS00YmYyLWI5ZTUtZjZhMzA1MTY5NDNhIiwiY2xpZW50X2lkIjoiYjRzIn0.OOG_mWnUYvWQYbBKeMf993qYxCK_vNvXqzR1y9342iI"
OUTPUT_FILE = "hdfc_results.json"

# --- Step 1: Get phone numbers from search API ---
def get_phone_numbers(search_key):
    url = SEARCH_URL.format(search_key)
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        phones = [
            user.get("phone")[3:] if user.get("phone", "").startswith("91-") else user.get("phone")
            for user in data if "phone" in user
        ]
        return phones
    else:
        print("Error fetching users:", response.status_code)
        return []

# --- Step 2: Get result from Buddy4Study API ---
def get_result(application_number="", email="", mobile=""):
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    payload = {
        "applicationNumber": application_number,
        "email": email,
        "mobile": mobile,
    }

    try:
        response = requests.post(RESULT_URL, headers=headers, json=payload)
        if response.status_code == 401:
            print(f"Unauthorized for {mobile}. Token may have expired.")
            return None
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching result for {mobile}: {e}")
        return None

# --- Step 3: Save result to JSON file ---
def save_result(data):
    # Skip empty responses
    if data == {
        "title": None,
        "publishDate": None,
        "count": 0,
        "logoFid": None,
        "awardees": []
    }:
        print("Skipped empty result")
        return

    all_data = []
    # Load existing file safely
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    all_data = json.loads(content)
        except json.JSONDecodeError:
            print(f"{OUTPUT_FILE} is corrupted. Overwriting.")

    # Append new data and save
    all_data.append(data)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)

    print("Saved result")

# --- Main ---
if __name__ == "__main__":
    key = input("User search: ")
    phone_numbers = get_phone_numbers(key)
    print(f"Found {len(phone_numbers)} phone numbers.")

    for phone in phone_numbers:
        print(f"Fetching result for: {phone}")
        result = get_result(mobile=phone)
        if result:
            save_result(result)
