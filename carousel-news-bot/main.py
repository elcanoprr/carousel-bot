import logging
import random
import sys
from datetime import datetime, timezone
from typing import Dict, List

from scraper import scrape_all
from generator import generate_carousel_script
from telegram_sender import send_to_telegram

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Rotate topic focus by time of day so 3 daily runs cover different angles
TOPIC_ROTATION = {
    "morning": ["inteligencia artificial", "tecnología e IA"],       # ~12 UTC
    "afternoon": ["redes sociales"],                                   # ~17 UTC
    "evening": ["creación de contenido", "tecnología e IA"],          # ~22 UTC
}


def get_time_slot() -> str:
    hour = datetime.now(timezone.utc).hour
    if hour < 15:
        return "morning"
    elif hour < 20:
        return "afternoon"
    return "evening"


def pick_article(articles: List[Dict]) -> Dict:
    slot = get_time_slot()
    preferred_topics = TOPIC_ROTATION[slot]
    logger.info(f"Slot de tiempo: {slot} → temas preferidos: {preferred_topics}")

    preferred = [
        a for a in articles
        if a.get("topic") in preferred_topics and len(a.get("summary", "")) > 40
    ]
    with_summary = [a for a in articles if len(a.get("summary", "")) > 40]
    pool = preferred or with_summary or articles

    return random.choice(pool)


def main():
    logger.info("=== Bot de carruseles iniciado ===")

    articles = scrape_all()
    if not articles:
        logger.error("No se encontraron artículos. Abortando.")
        sys.exit(1)

    logger.info(f"Total artículos encontrados: {len(articles)}")

    article = pick_article(articles)
    logger.info(f"Artículo seleccionado: [{article['source']}] {article['title']}")

    script = generate_carousel_script(article)
    logger.info("Script generado:\n" + script)

    success = send_to_telegram(script, article)
    if not success:
        logger.error("Fallo al enviar a Telegram.")
        sys.exit(1)

    logger.info("=== Listo ===")


if __name__ == "__main__":
    main()
