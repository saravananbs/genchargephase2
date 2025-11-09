import pyotp
from ..core.config import settings
from .messages import send_sms_fast2sms

def generate_otp():
    totp = pyotp.TOTP(settings.OTP_SECRET, interval=60 * settings.OTP_EXPIRE_MINUTES)
    return totp.now()

def verify_otp(input_otp: str, stored_otp: str):
    return input_otp == stored_otp 

async def send_otp(to: str, otp: str):
    await send_sms_fast2sms(message=f"Your otp to login to Gencharge is {otp}", to_phone=to)
