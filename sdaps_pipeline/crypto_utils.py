import json
import os
from pathlib import Path

from jwcrypto import jwk, jwe
from jwcrypto.common import json_encode

# Paths are env-driven so the sender and the receiver can point at different
# files (the sender only ever needs the public key). Defaults live outside
# the repo so a key never accidentally gets committed.
PRIVATE_KEY_PATH = Path(os.environ.get(
    "SDAPS_PRIVATE_KEY_PATH", os.path.expanduser("~/.secrets/sdaps/sdaps_private.pem")
))
PUBLIC_KEY_PATH = Path(os.environ.get(
    "SDAPS_PUBLIC_KEY_PATH", os.path.expanduser("~/.secrets/sdaps/sdaps_public.pem")
))

HEADERS = {
    "alg": "RSA-OAEP-256",
    "enc": "A256GCM",
}


def load_public_key(path: Path) -> jwk.JWK:
    return jwk.JWK.from_pem(path.read_bytes())


def load_private_key(path: Path) -> jwk.JWK:
    return jwk.JWK.from_pem(path.read_bytes())


def encrypt_json(data: dict, recipient_public_key: jwk.JWK) -> str:
    payload = json.dumps(data, default=str).encode("utf-8")
    jwe_token = jwe.JWE(
        plaintext=payload,
        protected=json_encode(HEADERS),
        recipient=recipient_public_key,
    )
    return jwe_token.serialize(compact=True)


def decrypt_json(token: str, recipient_private_key: jwk.JWK) -> dict:
    decrypted = jwe.JWE()
    decrypted.deserialize(token, key=recipient_private_key)
    return json.loads(decrypted.payload.decode("utf-8"))
