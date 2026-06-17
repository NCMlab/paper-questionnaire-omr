import json
import os
import stat
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


def generate_keypair(private_path: Path, public_path: Path) -> None:
    keypair = jwk.JWK.generate(kty='RSA', size=2048)
    private_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.parent.mkdir(parents=True, exist_ok=True)
    private_path.write_bytes(keypair.export_to_pem(private_key=True, password=None))
    private_path.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 600, owner read/write only
    public_path.write_bytes(keypair.export_to_pem(private_key=False))


def load_public_key(path: Path) -> jwk.JWK:
    return jwk.JWK.from_pem(path.read_bytes())


def load_private_key(path: Path) -> jwk.JWK:
    return jwk.JWK.from_pem(path.read_bytes())


def encrypt_json(data: dict, recipient_public_key: jwk.JWK) -> str:
    payload = json.dumps(data).encode("utf-8")
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


if __name__ == "__main__":
    if not PRIVATE_KEY_PATH.exists():
        generate_keypair(PRIVATE_KEY_PATH, PUBLIC_KEY_PATH)
        print(f"Generated new key pair: {PRIVATE_KEY_PATH} / {PUBLIC_KEY_PATH}")

    public_key = load_public_key(PUBLIC_KEY_PATH)
    private_key = load_private_key(PRIVATE_KEY_PATH)

    data = {"subject_id": 42, "score": 87.5}

    encrypted_data = encrypt_json(data, public_key)
    print("Encrypted JWE:", encrypted_data)

    # URL on Laptop to send the data to
    # http://127.0.0.1:9000/publix/Jekptz4UTHz?UsageType=DataReceive&Battery=99001&Data=encrypted_data

    decrypted_data = decrypt_json(encrypted_data, private_key)
    print("Decrypted JSON:", decrypted_data)
