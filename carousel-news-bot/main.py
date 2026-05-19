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
    # Platforms
    "instagram", "tiktok", "youtube", "twitter", "facebook", "linkedin",
    "pinterest", "snapchat", "threads", "reels", "shorts", "x.com",
    # Creator tools & gear
    "creator", "content", "influencer", "ugc", "brand deal", "sponsorship",
    "camera", "lens", "microphone", "lighting", "gimbal", "drone", "tripod",
    "sony", "canon", "nikon", "gopro", "dji",
    # Software & apps
    "capcut", "premiere", "davinci", "final cut", "adobe", "canva",
    "editing", "scheduling", "analytics",
    # AI tools for creators
    "ai tool", "chatgpt", "midjourney", "sora", "runway", "ai video",
    "ai image", "generative ai", "text to video", "text to image",
    # Growth & monetization
    "algorithm", "viral", "engagement", "follower", "subscriber",
    "monetization", "revenue", "views", "reach", "impressions",
    # General social / platforms
    "social media", "social network", "platform", "app update", "new feature",
    "live stream", "podcast", "newsletter",
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
