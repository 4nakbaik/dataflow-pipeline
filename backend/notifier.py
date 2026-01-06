import os
import logging
import requests
from typing import Optional

# Konfigurasi Logging
logger = logging.getLogger(__name__)

def send_telegram_alert(message: str) -> bool:
    """
    Mengirim pesan teks ke Telegram menggunakan Bot API.
    
    Args:
        message (str): Isi pesan yang akan dikirim (mendukung Markdown).
        
    Returns:
        bool: True jika berhasil, False jika gagal.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        logger.warning("Telegram credentials (TOKEN/CHAT_ID) not found in .env")
        return False

    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(api_url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Telegram alert sent successfully.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Telegram alert: {e}")
        return False