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

# 1. API សម្រាប់ User ធម្មតា (រាប់ View)
@app.route("/api/visit", methods=["POST"])
def add_view():
    # FIXED: ប្រើ is None ជំនួស if not
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
        print(f"Error adding view: {e}")
        return jsonify({"error": str(e)}), 500

# 2. API សម្រាប់យកចំនួន View (មិនបូកថែម) - សម្រាប់ Admin Dashboard
@app.route("/api/stats", methods=["GET"])
def get_stats():
    # FIXED: ប្រើ is None ជំនួស if not
    if views_collection is None: 
        return jsonify({"count": 0})
    
    try:
        doc = views_collection.find_one({"_id": "global_counter"})
        count = doc["count"] if doc else 0
        return jsonify({"count": count})
    except Exception as e:
        print(f"Error getting stats: {e}")
        return jsonify({"error": str(e)}), 500

# 3. API សម្រាប់ Reset Views (ត្រូវការ Password)
@app.route("/api/admin/reset-views", methods=["POST"])
def reset_views():
    # FIXED: ប្រើ is None
    if views_collection is None:
        return jsonify({"success": False, "message": "Database disconnected"}), 500

    data = request.json
    password = data.get("password")

    # ឆែក Password
    if password != ADMIN_PASSWORD:
        return jsonify({"success": False, "message": "Incorrect Password!"}), 401

    try:
        # Reset ទៅ 0
        views_collection.update_one(
            {"_id": "global_counter"},
            {"$set": {"count": 0}},
            upsert=True
        )
        return jsonify({"success": True, "message": "Views have been reset to 0."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# 4. API សម្រាប់ Login Check
@app.route("/api/admin/login", methods=["POST"])
def login():
    data = request.json
    if data.get("password") == ADMIN_PASSWORD:
        return jsonify({"success": True})
    return jsonify({"success": False}), 401

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)