import os
from fastapi import FastAPI, Header, HTTPException, Depends, status
from pydantic import BaseModel
from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv()

app = FastAPI(title="Telegram Notification Service")

# Configuration from .env
AUTH_KEY = os.getenv("AUTH_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

class Notification(BaseModel):
    message: str

async def verify_auth_key(x_auth_key: str = Header(None)):
    if x_auth_key != AUTH_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Authorization Key"
        )
    return x_auth_key

@app.post("/notify", status_code=status.HTTP_200_OK)
async def send_notification(notification: Notification, _ = Depends(verify_auth_key)):
    """
    Sends a message to the configured Telegram chat.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Telegram bot configuration is missing"
        )

    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": notification.message,
        "parse_mode": "HTML"  # Defaulting to HTML for better flexibility
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(telegram_url, json=payload)
            response.raise_for_status()
            return {"status": "success", "message": "Notification sent"}
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Telegram API error: {e.response.text}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred: {str(e)}"
            )

@app.get("/health")
async def health_check():
    return {"status": "ok"}
