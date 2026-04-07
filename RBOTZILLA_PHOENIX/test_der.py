import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

secret = "Fp9O7lkldCYUc2Mil0isiHiOu1PHZF5+T5Padyz14D0lvnY/9NafLdp+W4cpZYB57VlTJgiKDgaJEcD05nXM+g=="

try:
    decoded = base64.b64decode(secret)
    print(f"Decoded length: {len(decoded)} bytes")
    # Is it raw ASN.1 DER?
    private_key = serialization.load_der_private_key(decoded, password=None, backend=default_backend())
    print("Successfully loaded as DER private key!")
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    print("PEM:", pem.decode('utf-8'))
except Exception as e:
    print(f"Failed to load as DER: {e}")
