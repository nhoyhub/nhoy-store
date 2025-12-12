import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv
from bson.objectid import ObjectId

# --- CONFIGURATION ---
load_dotenv()
app = Flask(__name__)
CORS(app)  # Enables connection from HTML to Python

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

db = None
views_collection = None
apps_collection = None
settings_collection = None # <--- NEW: For storing Locker Status

if MONGO_URI:
    try:
        client = MongoClient(MONGO_URI)
        db = client["nhoyhub_db"]
        views_collection = db["site_views"]
        apps_collection = db["apps_data"]
        settings_collection = db["site_settings"] # <--- Initialize Settings DB
        print("✅ MongoDB Connected")
    except Exception as e:
        print(f"❌ DB Error: {e}")

# --- ROUTES ---

@app.route('/')
def home():
    return "NhoyHub API is Running!"

# --- VIEW COUNTER ---
@app.route("/api/visit", methods=["POST"])
def add_view():
    if views_collection is None: return jsonify({"count": 0})
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

@app.route("/api/stats", methods=["GET"])
def get_stats():
    if views_collection is None: return jsonify({"count": 0})
    try:
        doc = views_collection.find_one({"_id": "global_counter"})
        count = doc["count"] if doc else 0
        return jsonify({"count": count})
    except:
        return jsonify({"count": 0})

# --- ADMIN AUTH & UTILS ---
@app.route("/api/admin/login", methods=["POST"])
def login():
    data = request.json
    if data.get("password") == ADMIN_PASSWORD:
        return jsonify({"success": True})
    return jsonify({"success": False}), 401

@app.route("/api/admin/update-views", methods=["POST"])
def update_view_count():
    data = request.json
    if data.get("password") != ADMIN_PASSWORD: return jsonify({"success": False}), 401
    
    views_collection.update_one(
        {"_id": "global_counter"},
        {"$set": {"count": int(data.get("new_count"))}},
        upsert=True
    )
    return jsonify({"success": True})

# --- NEW: LOCKER SYSTEM SETTINGS ---

# 1. Get Locker Status (Used by Index and Admin)
@app.route("/api/admin/setting/locker", methods=["GET"])
def get_locker_status():
    if settings_collection is None: return jsonify({"enabled": True})
    try:
        doc = settings_collection.find_one({"_id": "locker_config"})
        # Default to True (Locked) if no setting exists yet
        is_enabled = doc["enabled"] if doc else True
        return jsonify({"enabled": is_enabled})
    except:
        return jsonify({"enabled": True})

# 2. Update Locker Status (Admin Only)
@app.route("/api/admin/setting/locker", methods=["POST"])
def update_locker_status():
    data = request.json
    if data.get("password") != ADMIN_PASSWORD: return jsonify({"success": False}), 401
    
    new_status = data.get("enabled") # True or False
    
    settings_collection.update_one(
        {"_id": "locker_config"},
        {"$set": {"enabled": new_status}},
        upsert=True
    )
    return jsonify({"success": True, "enabled": new_status})


# --- APP MANAGEMENT (DYNAMIC CONTENT) ---

# 1. Get All Apps (Public)
@app.route("/api/apps", methods=["GET"])
def get_apps():
    if apps_collection is None: return jsonify([])
    apps = []
    # Fetch all and convert ObjectId to string
    for doc in apps_collection.find():
        doc['_id'] = str(doc['_id'])
        apps.append(doc)
    return jsonify(apps)

# 2. Add App (Admin Only)
@app.route("/api/admin/add-app", methods=["POST"])
def add_app():
    data = request.json
    if data.get("password") != ADMIN_PASSWORD:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    new_app = {
        "category": data.get("category"), 
        "title": data.get("title"),
        "version": data.get("version"),
        "status": data.get("status"),
        "color": data.get("color"),
        "img": data.get("img"),
        "desc": data.get("desc"),
        "link": data.get("link")
    }
    
    result = apps_collection.insert_one(new_app)
    return jsonify({"success": True, "message": "App Added", "id": str(result.inserted_id)})

# 3. Edit App (Admin Only) - NEW: WAS MISSING
@app.route("/api/admin/edit-app", methods=["POST"])
def edit_app():
    data = request.json
    if data.get("password") != ADMIN_PASSWORD:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    app_id = data.get("id")
    update_data = {
        "category": data.get("category"), 
        "title": data.get("title"),
        "version": data.get("version"),
        "status": data.get("status"),
        "color": data.get("color"),
        "img": data.get("img"),
        "desc": data.get("desc"),
        "link": data.get("link")
    }
    
    apps_collection.update_one({"_id": ObjectId(app_id)}, {"$set": update_data})
    return jsonify({"success": True, "message": "App Updated"})

# 4. Delete App (Admin Only)
@app.route("/api/admin/delete-app", methods=["POST"])
def delete_app():
    data = request.json
    if data.get("password") != ADMIN_PASSWORD:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    app_id = data.get("id")
    apps_collection.delete_one({"_id": ObjectId(app_id)})
    return jsonify({"success": True, "message": "App Deleted"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
