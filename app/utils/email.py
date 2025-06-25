import aiosmtplib

from email.message import EmailMessage
import os

async def send_verification_email(to_email: str, token: str):
    msg = EmailMessage()
    msg["From"] = os.getenv("EMAIL_FROM")
    msg["To"] = to_email
    msg["Subject"] = "Verify your email"

    verification_link = f"http://localhost:8000/client/verify-email?token={token}"
    msg.set_content(f"Click the link to verify your email: {verification_link}")

    await aiosmtplib.send(
        msg,
        hostname=os.getenv("EMAIL_HOST"),
        port=int(os.getenv("EMAIL_PORT")),
        start_tls=True,
        username=os.getenv("EMAIL_USER"),
        password=os.getenv("EMAIL_PASSWORD")
    )
