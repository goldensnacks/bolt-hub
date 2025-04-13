from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

private_key_path = "mkt_key.txt"
def load_private_key_from_file(file_path):
    with open(file_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,  # or provide a password if your key is encrypted
            backend=default_backend()
        )
    return private_key

PRIVATE_KEY = load_private_key_from_file(private_key_path)
print(PRIVATE_KEY)