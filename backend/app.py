import os
import sqlite3
from flask import Flask, jsonify, render_template, g, send_from_directory
from flask_cors import CORS

# --- CONFIGURATION & PATHS ---
# Get the absolute path of the current file (app.py)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Go up one level to the NHOYSTORE folder
PARENT_DIR = os.path.dirname(CURRENT_DIR)

# Define the path to the frontend folder
FRONTEND_DIR = os.path.join(PARENT_DIR, "frontend")

# Define the database path (stored in backend folder)
DB_PATH = os.path.join(CURRENT_DIR, "views.db")

# Initialize Flask
# We tell Flask to look for HTML templates and Static files in the 'frontend' folder
app = Flask(__name__, template_folder=FRONTEND_DIR, static_folder=FRONTEND_DIR)
CORS(app) # Enable Cross-Origin Resource Sharing

# --- DATABASE MANAGEMENT ---
def get_db():
    """Connect to the database and return the connection object."""
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH, timeout=10)
        g.db.row_factory = sqlite3.Row # Access columns by name
    return g.db

@app.teardown_appcontext
def close_db(exc):
    """Close the database connection when the request finishes."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize the database table if it doesn't exist."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # Create table if not exists
            conn.execute("""
                CREATE TABLE IF NOT EXISTS site_views (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    count INTEGER NOT NULL DEFAULT 0
                );
            """)
            # Initialize counter at 0 if the table is empty
            cursor = conn.execute("SELECT count(*) FROM site_views WHERE id = 1;")
            if cursor.fetchone()[0] == 0:
                conn.execute("INSERT INTO site_views (id, count) VALUES (1, 0);")
            conn.commit()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Database Init Error: {e}")

# --- ROUTES ---

@app.route("/")
def index():
    """Serve the index.html file."""
    return render_template("index.html")

# Serve other static files (images/css if you have them locally)
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(FRONTEND_DIR, path)

@app.route("/api/visit", methods=["POST"])
def add_view():
    """Increment the view counter and return the new count."""
    db = get_db()
    new_count = 0
    try:
        # Use a transaction to safely increment
        cur = db.cursor()
        cur.execute("BEGIN IMMEDIATE")
        cur.execute("UPDATE site_views SET count = count + 1 WHERE id = 1")
        cur.execute("SELECT count FROM site_views WHERE id = 1")
        row = cur.fetchone()
        db.commit()
        
        if row:
            new_count = row['count']
            
    except Exception as e:
        db.rollback()
        print(f"Error updating views: {e}")
        # If error, try to just read the current count
        try:
            cur = db.execute("SELECT count FROM site_views WHERE id = 1")
            row = cur.fetchone()
            if row: new_count = row['count']
        except:
            pass

    return jsonify({"count": new_count})

# --- ENTRY POINT ---
if __name__ == "__main__":
    # Check if frontend folder exists before starting
    if not os.path.exists(FRONTEND_DIR):
        print(f"Error: Frontend folder not found at {FRONTEND_DIR}")
    else:
        init_db()
        print(f"Server starting on http://localhost:5000")
        # debug=True allows the server to restart automatically when you change code
        app.run(host="0.0.0.0", port=5000, debug=True)