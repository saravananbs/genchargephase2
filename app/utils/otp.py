import pyotp
from ..core.config import settings
from .messages import send_sms_fast2sms

def generate_otp():
    """
    Generate a time-based one-time password (OTP).

    Uses application `OTP_SECRET` and `OTP_EXPIRE_MINUTES` from settings to
    create a TOTP and return the current OTP value as a string.

    Returns:
        str: A numeric OTP string.

    Raises:
        Exception: Propagates any errors from the `pyotp` library or missing settings.
    """
    totp = pyotp.TOTP(settings.OTP_SECRET, interval=60 * settings.OTP_EXPIRE_MINUTES)
    return totp.now()

def verify_otp(input_otp: str, stored_otp: str):
    """
    Verify whether an input OTP matches a stored OTP value.

    Args:
        input_otp (str): The OTP provided by the user.
        stored_otp (str): The OTP stored/expected for verification.

    Returns:
        bool: True if the OTPs match, False otherwise.
    """
    return input_otp == stored_otp 

async def send_otp(to: str, otp: str):
    """
    Send an OTP via SMS to the specified phone number.

    This is an async wrapper around the SMS sender used by the application.

    Args:
        to (str): Recipient phone number (any format accepted by normalization).
        otp (str): OTP string to include in the message.

    Returns:
        dict|None: The underlying SMS sender's response dictionary when available.

    Raises:
        RuntimeError: If SMS provider configuration is missing (propagated from sender).
    """
    await send_sms_fast2sms(message=f"Your otp to login to Gencharge is {otp}", to_phone=to)
