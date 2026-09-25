import os
import psycopg2
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS keys (
            key TEXT PRIMARY KEY,
            expiry DATE NOT NULL,
            active BOOLEAN DEFAULT TRUE
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

init_db()

@app.route("/validate", methods=["POST"])
def validate():
    data = request.json
    key  = data.get("key", "")
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("SELECT expiry, active FROM keys WHERE key = %s", (key,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return jsonify({"valid": False, "reason": "Invalid key"})
    expiry, active = row
    if not active:
        return jsonify({"valid": False, "reason": "Key revoked"})
    if datetime.now().date() > expiry:
        return jsonify({"valid": False, "reason": "Key expired"})
    return jsonify({"valid": True, "expiry": str(expiry)})

@app.route("/add", methods=["POST"])
def add_key():
    data   = request.json
    secret = data.get("secret", "")
    if secret != os.environ.get("ADMIN_SECRET"):
        return jsonify({"error": "Unauthorized"}), 401
    key    = data.get("key")
    expiry = data.get("expiry")
    conn   = get_db()
    cur    = conn.cursor()
    cur.execute("INSERT INTO keys (key, expiry) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET expiry = %s, active = TRUE",
                (key, expiry, expiry))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"success": True, "key": key, "expiry": expiry})

@app.route("/revoke", methods=["POST"])
def revoke_key():
    data   = request.json
    secret = data.get("secret", "")
    if secret != os.environ.get("ADMIN_SECRET"):
        return jsonify({"error": "Unauthorized"}), 401
    key  = data.get("key")
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("UPDATE keys SET active = FALSE WHERE key = %s", (key,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"success": True, "key": key})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
