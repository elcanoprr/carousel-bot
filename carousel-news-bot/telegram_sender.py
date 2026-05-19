import os
import requests
import logging
from datetime import datetime, timezone
from typing import Dict

logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

MAX_TELEGRAM_CHARS = 4000


def build_message(script: str, article: Dict) -> str:
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    title_short = article["title"][:70] + "..." if len(article["title"]) > 70 else article["title"]
    url = article.get("url") or ""

    header_lines = [
        f"🗞️ *CARRUSEL LISTO* | {now}",
        f"📰 Fuente: {article['source']}",
    ]
    if url:
        header_lines.append(f"🔗 [Ver noticia]({url})")
    header_lines.append("━━━━━━━━━━━━━━━━━━━━\n")

    footer = "\n━━━━━━━━━━━━━━━━━━━━\n✅ _Script generado automáticamente_"

    header = "\n".join(header_lines)
    message = header + script + footer

    # Truncate if over Telegram limit
    if len(message) > MAX_TELEGRAM_CHARS:
        message = message[:MAX_TELEGRAM_CHARS - 3] + "..."

    return message


def send_to_telegram(script: str, article: Dict) -> bool:
    message = build_message(script, article)
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }
    try:
        r = requests.post(TELEGRAM_API, json=payload, timeout=15)
        if r.status_code == 200:
            logger.info("Mensaje enviado a Telegram")
            return True
        else:
            logger.error(f"Telegram error {r.status_code}: {r.text}")
            # Retry without markdown if parse error
            if r.status_code == 400:
                payload["parse_mode"] = ""
                payload["text"] = build_message(script, article).replace("*", "").replace("_", "")
                r2 = requests.post(TELEGRAM_API, json=payload, timeout=15)
                return r2.status_code == 200
            return False
    except Exception as e:
        logger.error(f"Error enviando a Telegram: {e}")
        return False
