import os

import requests

from crypto_utils import (
    PRIVATE_KEY_PATH,
    PUBLIC_KEY_PATH,
    decrypt_json,
    encrypt_json,
    load_private_key,
    load_public_key,
)

# Standalone receiver (sdaps_pipeline/receive_app.py), not the JATOS server.
RECEIVER_URL = os.environ.get("SDAPS_RECEIVER_URL", "http://127.0.0.1:9001/receive")


if __name__ == "__main__":
    public_key = load_public_key(PUBLIC_KEY_PATH)
    private_key = load_private_key(PRIVATE_KEY_PATH)

    data = json_array
    encrypted_data = encrypt_json(data, public_key)
    print("Encrypted JWE:", encrypted_data)

    decrypted_data = decrypt_json(encrypted_data, private_key)
    print("Decrypted JSON:", decrypted_data)

    response = requests.post(RECEIVER_URL, data=encrypted_data)

    # 3. Process the response
    print("Status Code:", response.status_code)
    print("Response Body:", response.json())



# OK, so there needs to be receiving "app" listener/flask for the json data to be
# received via a post command.