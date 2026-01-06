from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import requests
import os
import json
from dotenv import load_dotenv, set_key

load_dotenv()

app = Flask(__name__)
CORS(app)

# ================= CONFIG =================
ENV_FILE = ".env"
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

USER_SEARCH_URL = "https://sitareuniv.digiicampus.com/rest/users/search/all"
CLOUD_FRONT_BASE = "https://dli6r6oycdqaz.cloudfront.net/"
DEFAULT_PROFILE_IMG = "https://d1reij146f0v46.cloudfront.net/version-1757958587/images/profile.png"

# ================= TOKEN HELPERS =================
def get_auth_token():
    return os.getenv("AUTH_TOKEN")

def set_auth_token(token):
    set_key(ENV_FILE, "AUTH_TOKEN", token)
    os.environ["AUTH_TOKEN"] = token

# ================= UTIL =================
def convert_photo_url(photo):
    if not photo:
        return DEFAULT_PROFILE_IMG
    if "##" in photo:
        photo = photo.split("##", 1)[1]
    if not photo.startswith("http"):
        photo = CLOUD_FRONT_BASE + photo
    return photo

# ================= ROUTES =================

@app.route("/set_auth_token", methods=["POST"])
def set_token():
    data = request.get_json()
    token = data.get("token", "").strip()

    if not token:
        return jsonify({"error": "Token missing"}), 400

    set_auth_token(token)
    return jsonify({"message": "Auth token saved successfully"})

# -------------------------------------------------

@app.route("/search_users", methods=["GET"])
def search_users():
    key = request.args.get("key", "").strip()
    if not key:
        return jsonify({"error": "Missing search key"}), 400

    token = get_auth_token()
    if not token:
        return jsonify({"error": "Auth token not set"}), 401

    headers = {
        "Auth-Token": token,
        "User-Agent": "Mozilla/5.0"
    }

    try:
        r = requests.get(USER_SEARCH_URL, params={"key": key}, headers=headers)

        if r.status_code in (401, 403):
            return jsonify({"error": "Invalid or expired token"}), 403

        r.raise_for_status()
        users = r.json()

        # ---- structured output ----
        result = {
            "phones": [],
            "registration_ids": [],
            "emails": [],
            "names": [],
            "ukids": [],
            "user_types": [],
            "users": []
        }

        for u in users:
            phone = u.get("phone")
            if phone:
                result["phones"].append(phone[3:] if phone.startswith("91-") else phone)

            if u.get("registrationId"):
                result["registration_ids"].append(u["registrationId"])

            if u.get("email"):
                result["emails"].append(u["email"])

            if u.get("name"):
                result["names"].append(u["name"])

            if u.get("ukid"):
                result["ukids"].append(u["ukid"])

            if u.get("userType"):
                result["user_types"].append(u["userType"])

            result["users"].append({
                "name": u.get("name"),
                "email": u.get("email"),
                "registrationId": u.get("registrationId"),
                "phone": phone,
                "ukid": u.get("ukid"),
                "userType": u.get("userType"),
                "photo": convert_photo_url(u.get("photo"))
            })

        # ---- save files ----
        base = os.path.join(OUTPUT_DIR, key)

        with open(base + "_phones.txt", "w") as f:
            f.write("\n".join(result["phones"]))

        with open(base + "_registration_ids.txt", "w") as f:
            f.write("\n".join(map(str, result["registration_ids"])))

        with open(base + "_full.json", "w") as f:
            json.dump(result["users"], f, indent=2)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------------------------------

@app.route("/download", methods=["GET"])
def download_file():
    key = request.args.get("key")
    filetype = request.args.get("type")

    file_map = {
        "phones": f"{key}_phones.txt",
        "reg": f"{key}_registration_ids.txt",
        "full": f"{key}_full.json"
    }

    if filetype not in file_map:
        return jsonify({"error": "Invalid file type"}), 400

    path = os.path.join(OUTPUT_DIR, file_map[filetype])
    return send_file(path, as_attachment=True)

# ================= MAIN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
