from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Add your keys here — "KEY": "YYYY-MM-DD expiry"
KEYS = {
    "TESTKEY-1234": "2027-12-31",
    "TESTKEY-5678": "2027-12-31",
}

@app.route("/validate", methods=["POST"])
def validate():
    data = request.json
    key = data.get("key", "")
    
    if key not in KEYS:
        return jsonify({"valid": False, "reason": "Invalid key"})
    
    expiry = datetime.strptime(KEYS[key], "%Y-%m-%d")
    if datetime.now() > expiry:
        return jsonify({"valid": False, "reason": "Key expired"})
    
    return jsonify({"valid": True, "expiry": KEYS[key]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
