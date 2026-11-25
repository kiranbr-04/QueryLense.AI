import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.core.config import settings

def _get_fernet() -> Fernet:
    key_str = settings.ENCRYPTION_KEY
    try:
        # If already 32-byte base64 valid key
        return Fernet(key_str.encode() if isinstance(key_str, str) else key_str)
    except Exception:
        # Derive valid Fernet key from any string
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"querylens_static_salt_for_key_derivation",
            iterations=100_000,
        )
        derived = base64.urlsafe_b64encode(kdf.derive(key_str.encode()))
        return Fernet(derived)

def encrypt_secret(plain_text: str) -> str:
    """Encrypt a secret string (e.g. database password or API token)."""
    if not plain_text:
        return ""
    f = _get_fernet()
    return f.encrypt(plain_text.encode("utf-8")).decode("utf-8")

def decrypt_secret(cipher_text: str) -> str:
    """Decrypt an encrypted secret string. Returns empty string if empty or invalid."""
    if not cipher_text:
        return ""
    try:
        f = _get_fernet()
        return f.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
    except Exception as e:
        return f"<decryption-error: {str(e)}>"
