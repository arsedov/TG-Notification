import os
import logging
from fastapi import FastAPI, Header, HTTPException, Depends, status, Request
from pydantic import BaseModel
from dotenv import load_dotenv
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(title="Telegram Notification Service")

# Configuration from .env
AUTH_KEY = os.getenv("AUTH_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Check config on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Service starting up...")
    if not AUTH_KEY:
        logger.warning("AUTH_KEY is not set! Service will be wide open or reject everything.")
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is missing!")
    if not TELEGRAM_CHAT_ID:
        logger.error("TELEGRAM_CHAT_ID is missing!")

class Notification(BaseModel):
    message: str

async def verify_auth_key(request: Request, x_auth_key: str = Header(None)):
    if x_auth_key != AUTH_KEY:
        logger.warning(f"Unauthorized access attempt from {request.client.host}. Key: {x_auth_key}")
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
    logger.info(f"Received notification request: {notification.message[:50]}...")

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Telegram configuration missing in .env")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Telegram bot configuration is missing"
        )

    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": notification.message,
        "parse_mode": "HTML"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(telegram_url, json=payload, timeout=10.0)
            logger.info(f"Telegram API response: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Telegram error details: {response.text}")
            
            response.raise_for_status()
            return {"status": "success", "message": "Notification sent"}
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Telegram: {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Telegram API error: {e.response.text}"
            )
        except Exception as e:
            logger.exception("Unexpected error while sending to Telegram")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred: {str(e)}"
            )

@app.get("/health")
async def health_check():
    return {"status": "ok", "config": {
        "auth_key_set": bool(AUTH_KEY),
        "bot_token_set": bool(TELEGRAM_BOT_TOKEN),
        "chat_id_set": bool(TELEGRAM_CHAT_ID)
    }}
