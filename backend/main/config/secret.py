import os
from base64 import b64decode, b64encode

import bcrypt
from jsons import Optional


def get_secret_str(secret_name: str) -> Optional[str]:
    """
    Gets a secret, if it exists. Otherwise, returns None
    """
    return os.getenv(secret_name)


def overwrite_secret_str(secret_name: str, secret_value: str):
    """
    Will overwrite the secret, even if there already is a secret present for the given secret_name
    """
    os.environ[secret_name] = secret_value


def get_secret_bytes(secret_name: str) -> Optional[bytes]:
    """
    Gets a secret, if it exists. Otherwise, return None
    """
    secret_str = os.getenv(secret_name)
    if not secret_str:
        return None
    return b64decode(secret_str.encode("utf-8"))


def overwrite_secret_bytes(secret_name: str, secret_value: bytes):
    """
    Will overwrite the secret, even if there already is a secret preseent for the given secret_name
    """
    os.environ[secret_name] = b64encode(secret_value).decode("utf-8")


def gen_salt_or_pepper() -> bytes:
    return bcrypt.gensalt()
