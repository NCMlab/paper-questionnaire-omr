import json
import os
from datetime import datetime

from flask import Flask, request
import mysql.connector

from crypto_utils import PRIVATE_KEY_PATH, decrypt_json, load_private_key

RECEIVED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "received_data")

# Same database JATOS itself uses (see jatos.conf's jatos.db.* keys) — host/db/user
# match that file, but the password is never hardcoded here, only read from the
# environment, so it can't end up committed to the repo.
JATOS_DB_CONFIG = {
    "host": os.environ.get("JATOS_DB_HOST", "localhost"),
    "port": int(os.environ.get("JATOS_DB_PORT", "3306")),
    "database": os.environ.get("JATOS_DB_NAME", "jatos"),
    "user": os.environ.get("JATOS_DB_USER", "jatosuser"),
    "password": os.environ["JATOS_DB_PASSWORD"],
}

app = Flask(__name__)
private_key = load_private_key(PRIVATE_KEY_PATH)


def insert_into_jatos_db(data: dict) -> None:
    conn = mysql.connector.connect(**JATOS_DB_CONFIG)
    try:
        cursor = conn.cursor()
        # TODO: final INSERT statement(s), e.g.:
        # cursor.execute(
        #     "INSERT INTO <table> (<columns>) VALUES (%s, %s, ...)",
        #     (data["jatosWorkerID"], data["jatosBatchID"], ...),
        # )
        conn.commit()
    finally:
        conn.close()


@app.route("/receive", methods=["POST"])
def receive():
    token = request.get_data(as_text=True)
    if not token:
        return {"error": "empty body"}, 400

    try:
        data = decrypt_json(token, private_key)
    except Exception as exc:
        return {"error": "decryption failed: %s" % exc}, 400

    print(json.dumps(data, indent=4, default=str))

    os.makedirs(RECEIVED_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    out_path = os.path.join(RECEIVED_DIR, "%s.json" % timestamp)
    with open(out_path, "w") as f:
        json.dump(data, f, indent=4)

    try:
        insert_into_jatos_db(data)
        
    except Exception as exc:
        return {"error": "db insert failed: %s" % exc}, 500

    return {"status": "ok"}, 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9001, debug=False)
