"""
Etsy order.paid webhook receiver (FastAPI version).

Listens for Etsy's order.paid webhook, verifies the request signature,
and sends an email notification.

Run locally with:
    uvicorn app:app --host 0.0.0.0 --port 5000

Deploy behind any public HTTPS URL (Render, Railway, Fly.io, a VPS, etc.)
and register that URL as your Etsy webhook endpoint.
"""

import hashlib
import hmac
import os
import smtplib
from email.mime.text import MIMEText

from fastapi import FastAPI, Header, Request, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

# --- Config (set these as environment variables, never hardcode) ---
ETSY_WEBHOOK_SECRET = os.environ["ETSY_WEBHOOK_SECRET"]  # the whsec_... value

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ["SMTP_USER"]
SMTP_PASSWORD = os.environ["SMTP_PASSWORD"]
NOTIFY_EMAIL_TO = os.environ["NOTIFY_EMAIL_TO"]


def verify_signature(webhook_id: str, timestamp: str, raw_body: bytes, signature: str) -> bool:
    """
    Recompute the HMAC-SHA256 signature and compare it to the one Etsy sent.

    NOTE: confirm the exact signed-content format against Etsy's current
    docs (developer.etsy.com/documentation/essentials/webhooks) before
    going live -- webhook signing conventions have shifted before.
    """
    signed_content = f"{webhook_id}.{timestamp}.".encode() + raw_body
    expected = hmac.new(
        ETSY_WEBHOOK_SECRET.encode(),
        signed_content,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def send_email(subject: str, body: str) -> None:
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = NOTIFY_EMAIL_TO

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, [NOTIFY_EMAIL_TO], msg.as_string())


@app.post("/webhook/etsy")
async def etsy_webhook(
    request: Request,
    webhook_id: str = Header(default="", alias="webhook-id"),
    webhook_timestamp: str = Header(default="", alias="webhook-timestamp"),
    webhook_signature: str = Header(default="", alias="webhook-signature"),
):
    raw_body = await request.body()

    if not verify_signature(webhook_id, webhook_timestamp, raw_body, webhook_signature):
        raise HTTPException(status_code=401, detail="invalid signature")

    payload = await request.json()
    event_type = payload.get("event_type")

    if event_type == "order.paid":
        shop_id = payload.get("shop_id")
        resource_url = payload.get("resource_url")

        send_email(
            subject="New Etsy order paid!",
            body=(
                f"A new order was paid.\n\n"
                f"Shop ID: {shop_id}\n"
                f"Order details: {resource_url}\n"
            ),
        )

    # Always acknowledge quickly so Etsy doesn't retry unnecessarily
    return JSONResponse({"status": "received"}, status_code=200)


@app.get("/health")
async def health():
    return {"status": "ok"}
    
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))