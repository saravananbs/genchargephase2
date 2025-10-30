# utils/otp.py
import pyotp
from ..core.config import settings

def generate_otp():
    totp = pyotp.TOTP(settings.OTP_SECRET, interval=60 * settings.OTP_EXPIRE_MINUTES)
    return totp.now()

def verify_otp(input_otp: str, stored_otp: str):
    return input_otp == stored_otp 

async def send_otp(to: str, otp: str):
    # need to implement when frontend is inteoduced
    pass