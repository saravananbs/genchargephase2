# utils/security.py
from jose import jwt
from ..core.config import settings
from datetime import datetime, timedelta


def create_access_token(data: dict):
    """
    Create a JWT access token containing `data` and an expiration.

    Args:
        data (dict): A dictionary of claims to include in the token payload.

    Returns:
        str: Encoded JWT access token.

    Raises:
        jose.exceptions.JWTError: If encoding fails due to invalid key/algorithm.
    """
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """
    Create a JWT refresh token containing `data` and a longer expiration.

    Args:
        data (dict): A dictionary of claims to include in the token payload.

    Returns:
        str: Encoded JWT refresh token.

    Raises:
        jose.exceptions.JWTError: If encoding fails due to invalid key/algorithm.
    """
    to_encode = data.copy()
    expire = datetime.now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt