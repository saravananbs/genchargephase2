# utils/otp.py
import pyotp
from ..core.config import settings
import smtplib  # Or use Twilio for SMS

def generate_otp():
    totp = pyotp.TOTP(settings.OTP_SECRET, interval=60 * settings.OTP_EXPIRE_MINUTES)
    return totp.now()

def verify_otp(input_otp: str, stored_otp: str):
    return input_otp == stored_otp  # Or use totp.verify if time-based

async def send_otp(to: str, otp: str):
    # Implement email or SMS sending
    pass  # Placeholder