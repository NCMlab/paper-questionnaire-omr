import json
import os
from datetime import datetime

from flask import Flask, request

from crypto_utils import PRIVATE_KEY_PATH, decrypt_json, load_private_key

RECEIVED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "received_data")

app = Flask(__name__)
private_key = load_private_key(PRIVATE_KEY_PATH)


@app.route("/receive", methods=["POST"])
def receive():
    token = request.get_data(as_text=True)
    if not token:
        return {"error": "empty body"}, 400

    try:
        data = decrypt_json(token, private_key)
    except Exception as exc:
        return {"error": "decryption failed: %s" % exc}, 400

    os.makedirs(RECEIVED_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    out_path = os.path.join(RECEIVED_DIR, "%s.json" % timestamp)
    with open(out_path, "w") as f:
        json.dump(data, f, indent=4)

    return {"status": "ok"}, 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9001, debug=False)
