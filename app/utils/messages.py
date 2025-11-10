import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import re
from dotenv import load_dotenv
import aiohttp
import asyncio


load_dotenv()


def normalize_indian_number(number: str) -> str:
    """
    Normalize an Indian phone number string to a 10-digit numeric string.

    This removes non-digit characters and strips common country/leading
    zero prefixes such as "+91", "91" or a leading "0".

    Args:
        number (str): The input phone number to normalize.

    Returns:
        str: A 10-digit phone number string (digits only).

    Raises:
        ValueError: If the normalized result is not exactly 10 digits.
    """
    digits = re.sub(r'\D', '', number)
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    elif digits.startswith("0") and len(digits) == 11:
        digits = digits[1:]
    if len(digits) != 10:
        raise ValueError(f"Invalid Indian number: {number}")
    return digits


async def send_sms_fast2sms(message: str, to_phone: str) -> dict:
    """
    Send an SMS using the Fast2SMS API asynchronously.

    Args:
        message (str): The text message to send.
        to_phone (str): Recipient phone number in any common format.

    Returns:
        dict: A dictionary with keys:
            - "status": "success" or "failed".
            - "response": API response when successful.
            - "error": error details when failed.

    Raises:
        RuntimeError: If the Fast2SMS API key is not configured via environment.
    """
    FAST2SMS_API_URL = "https://www.fast2sms.com/dev/bulkV2"
    FAST2SMS_API_KEY = os.getenv("FAST2SMS_API_KEY")

    if not FAST2SMS_API_KEY:
        raise RuntimeError("Missing Fast2SMS configuration — set FAST2SMS_API_KEY")

    try:
        phone_number = normalize_indian_number(to_phone)
    except ValueError as e:
        return {"status": "failed", "error": str(e)}

    headers = {
        "authorization": FAST2SMS_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "sender_id": "FSTSMS",
        "message": message,
        "language": "english",
        "route": "v3",
        "numbers": phone_number
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(FAST2SMS_API_URL, headers=headers, json=payload) as resp:
                response_data = await resp.json()
                if resp.status == 200:
                    return {"status": "success", "response": response_data}
                else:
                    return {"status": "failed", "error": response_data}
        except Exception as e:
            print(f"Error sending SMS: {e}")
            print(f"send the message to {to_phone}")
            return {"status": "failed", "error": str(e)}


async def send_email(to_email: str, message: str, subject: str = "Gencharge"):
    """
    Send an email via Gmail SMTP.

    Note: This function expects Gmail credentials provided via environment
    variables `GMAIL_USER` and `GMAIL_PASS` (an app password is recommended).

    Args:
        to_email (str): Recipient email address.
        message (str): Plain-text email body.
        subject (str): Email subject. Defaults to "Gencharge".

    Returns:
        None

    Raises:
        EnvironmentError: If `GMAIL_USER` or `GMAIL_PASS` are not set.
        smtplib.SMTPException: For SMTP-level failures when sending.
    """
    gmail_user = os.getenv("GMAIL_USER")
    gmail_pass = os.getenv("GMAIL_PASS")

    if not gmail_user or not gmail_pass:
        raise EnvironmentError("Missing GMAIL_USER or GMAIL_PASS environment variables.")
    print(gmail_user, gmail_pass)

    msg = MIMEMultipart()
    msg['From'] = gmail_user
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain')) 

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            await server.starttls()  
            await server.login(gmail_user, gmail_pass)
            await server.send_message(msg)
        print(f"Email successfully sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")
