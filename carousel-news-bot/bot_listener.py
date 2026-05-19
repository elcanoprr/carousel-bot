import logging
import os
import random
import sys
from typing import Dict, List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, ContextTypes

from scraper import scrape_all
from generator import generate_carousel_script
from telegram_sender import send_to_telegram
from main import is_relevant, pick_article

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

# Tracks used article URLs to avoid repeating scripts
_used_urls: set = set()

# Keyword groups per category
CATEGORIES = {
    "instagram": ["instagram", "reels", "stories", "threads", "ig ", "meta ads", "instagram ads"],
    "contenido": ["content creator", "creador de contenido", "youtuber", "tiktoker", "tiktok", "youtube", "shorts", "viral", "ugc"],
    "edits": ["editing", "edición", "capcut", "premiere", "davinci resolve", "final cut", "after effects", "luts", "color grading", "motion graphics", "video edit"],
    "ai": ["artificial intelligence", "inteligencia artificial", "chatgpt", "claude", "midjourney", "sora", "runway", "ai tool", "ai video", "ai image", "generative ai", "automation", "machine learning"],
    "herramientas": ["camera", "cámara", "sony", "canon", "nikon", "fujifilm", "dji", "gopro", "gimbal", "drone", "microphone", "micrófono", "lighting", "iluminación", "ring light", "tripod", "lens", "stabilizer", "tool", "app", "software", "plugin"],
}

CATEGORY_LABELS = {
    "instagram": "Instagram",
    "contenido": "Creación de Contenido",
    "edits": "Edición de Video",
    "ai": "AI para Marketing",
    "herramientas": "Herramientas para Creadores",
}


def pick_fresh_article(articles: List[Dict], category: str = "") -> Optional[Dict]:
    global _used_urls

    if category and category in CATEGORIES:
        keywords = CATEGORIES[category]
        matching = [
            a for a in articles
            if any(kw in (a["title"] + " " + a.get("summary", "")).lower() for kw in keywords)
        ]
    else:
        matching = [a for a in articles if is_relevant(a)]

    if not matching:
        matching = articles

    # Exclude already-used articles
    fresh = [a for a in matching if a.get("url", "") not in _used_urls]

    # If all are used, reset history
    if not fresh:
        logger.info("Todos los artículos fueron usados — reseteando historial.")
        _used_urls.clear()
        fresh = matching

    # Prefer articles with summaries
    with_summary = [a for a in fresh if len(a.get("summary", "")) > 40]
    pool = with_summary if with_summary else fresh

    article = random.choice(pool)
    _used_urls.add(article.get("url", ""))
    return article


async def run_category(update: Update, category: str):
    label = CATEGORY_LABELS.get(category, category)
    await update.message.reply_text(f"🔍 Buscando noticias de *{label}*...", parse_mode="Markdown")

    articles = scrape_all()
    if not articles:
        await update.message.reply_text("No encontré noticias ahora mismo. Intenta en unos minutos.")
        return

    article = pick_fresh_article(articles, category)
    script = generate_carousel_script(article)
    send_to_telegram(script, article)


async def cmd_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await run_category(update, "instagram")

async def cmd_contenido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await run_category(update, "contenido")

async def cmd_edits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await run_category(update, "edits")

async def cmd_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await run_category(update, "ai")

async def cmd_herramientas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await run_category(update, "herramientas")

async def cmd_ahora(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚡ Generando carrusel de última hora...")
    articles = scrape_all()
    if not articles:
        await update.message.reply_text("No encontré noticias ahora mismo. Intenta en unos minutos.")
        return
    article = pick_fresh_article(articles)
    script = generate_carousel_script(article)
    send_to_telegram(script, article)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 *Bot de Carruseles activo*\n\n"
        "Elige una categoría:\n\n"
        "📸 /instagram — Noticias de Instagram\n"
        "🎥 /contenido — Creación de contenido\n"
        "✂️ /edits — Edición de video\n"
        "🤖 /ai — AI para marketing\n"
        "🛠️ /herramientas — Herramientas para creadores\n"
        "⚡ /ahora — Última noticia relevante",
        parse_mode="Markdown",
    )


async def scheduled_post():
    logger.info("Corriendo post programado...")
    articles = scrape_all()
    if not articles:
        logger.warning("Sin artículos en post programado.")
        return
    article = pick_fresh_article(articles)
    script = generate_carousel_script(article)
    send_to_telegram(script, article)


async def post_init(app: Application) -> None:
    # Register commands so they appear when user types "/"
    await app.bot.set_my_commands([
        BotCommand("instagram", "Noticias de Instagram"),
        BotCommand("contenido", "Noticias de creación de contenido"),
        BotCommand("edits", "Noticias sobre edición de video"),
        BotCommand("ai", "AI para marketing"),
        BotCommand("herramientas", "Herramientas para creadores de contenido"),
        BotCommand("ahora", "Última noticia relevante ahora mismo"),
    ])

    # Start scheduler inside the running event loop
    scheduler = AsyncIOScheduler()
    for utc_hour in [11, 13, 15, 18, 21, 23]:
        scheduler.add_job(scheduled_post, "cron", hour=utc_hour, minute=0)
    scheduler.start()
    logger.info("Scheduler y comandos configurados.")


def main():
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("ahora", cmd_ahora))
    app.add_handler(CommandHandler("instagram", cmd_instagram))
    app.add_handler(CommandHandler("contenido", cmd_contenido))
    app.add_handler(CommandHandler("edits", cmd_edits))
    app.add_handler(CommandHandler("ai", cmd_ai))
    app.add_handler(CommandHandler("herramientas", cmd_herramientas))

    logger.info("Bot iniciado.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
