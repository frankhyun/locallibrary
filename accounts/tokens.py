import base64
import hashlib
import hmac
import json
import time

from django.conf import settings


def _encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _decode(data):
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def create_token(user_id, token_type, lifetime):
    header = _encode(b'{"alg":"HS256","typ":"JWT"}')
    payload = _encode(json.dumps({"sub": str(user_id), "type": token_type, "exp": int(time.time()) + lifetime}).encode())
    signature = hmac.new(settings.SECRET_KEY.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
    return f"{header}.{payload}.{_encode(signature)}"


def decode_token(token, token_type):
    try:
        header, payload, signature = token.split(".")
        expected = hmac.new(settings.SECRET_KEY.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
        claims = json.loads(_decode(payload))
    except (ValueError, KeyError, TypeError, json.JSONDecodeError, base64.binascii.Error):
        return None
    if not hmac.compare_digest(signature, _encode(expected)):
        return None
    if claims.get("type") != token_type or claims.get("exp", 0) < time.time():
        return None
    return claims


def create_token_pair(user_id):
    return {
        "access": create_token(user_id, "access", 15 * 60),
        "refresh": create_token(user_id, "refresh", 7 * 24 * 60 * 60),
    }
