"""AES-256-GCM 암복호화 유틸 (WiFi 비밀번호 등 민감 정보 저장용)

SRS 4.2 보안 요구사항: 와이파이 비밀번호 AES-256 암호화 저장.
키는 환경변수 ``PATHWAVE_AES_KEY`` (base64, 32바이트)로 주입한다.
환경변수가 없으면 개발용으로 SECRET_KEY에서 32바이트 키를 파생한다.
"""
import base64
import hashlib
import os
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _load_key() -> bytes:
    raw = os.environ.get('PATHWAVE_AES_KEY', '')
    if raw:
        try:
            key = base64.b64decode(raw)
        except Exception:
            key = raw.encode()
        if len(key) == 32:
            return key
    # dev fallback: SECRET_KEY에서 SHA-256으로 32바이트 파생
    secret = os.environ.get('SECRET_KEY', 'pathwave-super-secret-key-2024')
    return hashlib.sha256(secret.encode()).digest()


_KEY = _load_key()
_NONCE_LEN = 12


def encrypt_secret(plaintext: str) -> str:
    """문자열을 AES-GCM으로 암호화하고 base64(nonce|ct) 형태로 반환."""
    if plaintext is None:
        return ''
    aes = AESGCM(_KEY)
    nonce = secrets.token_bytes(_NONCE_LEN)
    ct = aes.encrypt(nonce, plaintext.encode('utf-8'), None)
    return base64.urlsafe_b64encode(nonce + ct).decode('ascii')


def decrypt_secret(token: str) -> str:
    """``encrypt_secret`` 결과를 평문으로 복호화. 평문이 들어오면 그대로 반환(레거시 호환)."""
    if not token:
        return ''
    try:
        blob = base64.urlsafe_b64decode(token.encode('ascii'))
        nonce, ct = blob[:_NONCE_LEN], blob[_NONCE_LEN:]
        return AESGCM(_KEY).decrypt(nonce, ct, None).decode('utf-8')
    except Exception:
        # base64/GCM 복호화 실패 → 평문 레거시 데이터로 간주
        return token
