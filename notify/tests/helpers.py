import base64
import os

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def vapid_private_key() -> str:
    """A fresh VAPID private key as the raw 32 bytes, base64url: the form Vercel holds."""
    key = ec.generate_private_key(ec.SECP256R1())
    return b64(key.private_numbers().private_value.to_bytes(32, "big"))


def phone_keys() -> tuple:
    """What a browser's PushSubscription carries: its public key (p256dh) and a 16-byte secret (auth)."""
    key = ec.generate_private_key(ec.SECP256R1())
    point = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    return b64(point), b64(os.urandom(16))
