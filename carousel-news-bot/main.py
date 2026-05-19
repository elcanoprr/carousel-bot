import logging
import random
import sys
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

# Keywords that make an article relevant for a social media content creator
RELEVANT_KEYWORDS = [
    # Instagram
    "instagram", "reels", "stories", "ig ",
    # Cameras & gear
    "camera", "cámara", "sony", "canon", "nikon", "fujifilm", "lumix", "panasonic",
    "gopro", "dji", "lens", "lente", "gimbal", "drone",
    # Video tools & software
    "video", "capcut", "premiere", "davinci resolve", "final cut", "after effects",
    "luts", "color grading", "color correction", "editing", "edición",
    "microphone", "micrófono", "lighting", "iluminación", "ring light",
    "teleprompter", "stabilizer", "estabilizador",
    # Content creation
    "content creator", "creador de contenido", "youtuber", "tiktoker",
]


def is_relevant(article: Dict) -> bool:
    text = (article.get("title", "") + " " + article.get("summary", "")).lower()
    return any(kw in text for kw in RELEVANT_KEYWORDS)


def pick_article(articles: List[Dict]) -> Dict:
    relevant = [a for a in articles if is_relevant(a)]
    pool = relevant if relevant else articles
    # Prefer articles with a summary
    with_summary = [a for a in pool if len(a.get("summary", "")) > 40]
    return random.choice(with_summary if with_summary else pool)


def main():
    logger.info("=== Bot de carruseles iniciado ===")

    articles = scrape_all()
    if not articles:
        logger.error("No se encontraron artículos. Abortando.")
        sys.exit(1)

    relevant = [a for a in articles if is_relevant(a)]
    logger.info(f"Artículos totales: {len(articles)} | Relevantes: {len(relevant)}")

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
