import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()
app = Flask(__name__)
CORS(app)

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# Initialize DB variables
db = None
views_collection = None

if MONGO_URI:
    try:
        client = MongoClient(MONGO_URI)
        db = client["nhoyhub_db"]
        views_collection = db["site_views"]
        print("✅ MongoDB Connected")
    except Exception as e:
        print(f"❌ DB Error: {e}")

# --- ROUTES ---

@app.route('/')
def home():
    return "NhoyHub API is Running!"

# 1. API for User Visit (Increment Count)
@app.route("/api/visit", methods=["POST"])
def add_view():
    if views_collection is None: 
        return jsonify({"count": 0})
    
    try:
        updated = views_collection.find_one_and_update(
            {"_id": "global_counter"},
            {"$inc": {"count": 1}},
            upsert=True,
            return_document=True
        )
        return jsonify({"count": updated["count"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 2. API for Admin Dashboard (Get Count Only)
@app.route("/api/stats", methods=["GET"])
def get_stats():
    if views_collection is None: 
        return jsonify({"count": 0})
    
    try:
        doc = views_collection.find_one({"_id": "global_counter"})
        count = doc["count"] if doc else 0
        return jsonify({"count": count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 3. API to Reset Views to 0
@app.route("/api/admin/reset-views", methods=["POST"])
def reset_views():
    if views_collection is None:
        return jsonify({"success": False, "message": "Database disconnected"}), 500

    data = request.json
    password = data.get("password")

    if password != ADMIN_PASSWORD:
        return jsonify({"success": False, "message": "Incorrect Password!"}), 401

    try:
        views_collection.update_one(
            {"_id": "global_counter"},
            {"$set": {"count": 0}},
            upsert=True
        )
        return jsonify({"success": True, "message": "Views have been reset to 0."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# 4. API to Check Login
@app.route("/api/admin/login", methods=["POST"])
def login():
    data = request.json
    if data.get("password") == ADMIN_PASSWORD:
        return jsonify({"success": True})
    return jsonify({"success": False}), 401

# 5. NEW API: Manually Set View Count
@app.route("/api/admin/update-views", methods=["POST"])
def update_view_count():
    if views_collection is None:
        return jsonify({"success": False, "message": "Database disconnected"}), 500

    data = request.json
    password = data.get("password")
    new_count = data.get("new_count")

    # Check Password
    if password != ADMIN_PASSWORD:
        return jsonify({"success": False, "message": "Incorrect Password!"}), 401

    # Validate Input
    if new_count is None:
         return jsonify({"success": False, "message": "No number provided"}), 400

    try:
        # Update the count to the specific number
        views_collection.update_one(
            {"_id": "global_counter"},
            {"$set": {"count": int(new_count)}},
            upsert=True
        )
        return jsonify({"success": True, "message": f"Views updated to {new_count}"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == "__main__":
    # IMPORTANT: Use the PORT environment variable for Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)