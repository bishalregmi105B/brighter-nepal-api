"""Lightweight reversible URL cipher for API payload obfuscation."""
from __future__ import annotations

import base64
import os

PREFIX = 'bnenc:'
DEFAULT_KEY = 'bn-url-cipher-v1'


def _key_bytes() -> bytes:
    key = (os.getenv('URL_CIPHER_KEY') or '').strip() or DEFAULT_KEY
    raw = key.encode('utf-8')
    return raw if raw else DEFAULT_KEY.encode('utf-8')


def _xor_bytes(data: bytes, key: bytes) -> bytes:
    return bytes(byte ^ key[idx % len(key)] for idx, byte in enumerate(data))


def encrypt_url(value: str | None) -> str:
    raw = (value or '').strip()
    if not raw:
        return ''
    key = _key_bytes()
    encrypted = _xor_bytes(raw.encode('utf-8'), key)
    token = base64.urlsafe_b64encode(encrypted).decode('ascii').rstrip('=')
    return f'{PREFIX}{token}'


def decrypt_url(value: str | None) -> str:
    raw = (value or '').strip()
    if not raw:
        return ''
    if not raw.startswith(PREFIX):
        return raw
    token = raw[len(PREFIX):]
    if not token:
        return ''
    pad = '=' * (-len(token) % 4)
    payload = base64.urlsafe_b64decode(token + pad)
    key = _key_bytes()
    plain = _xor_bytes(payload, key)
    return plain.decode('utf-8')
