import logging
import os
import random
import sys

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from scraper import scrape_all
from generator import generate_carousel_script
from telegram_sender import send_to_telegram
from main import pick_article, is_relevant

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]


async def scheduled_post():
    logger.info("Corriendo post programado...")
    articles = scrape_all()
    if not articles:
        logger.warning("Sin artículos en post programado.")
        return
    article = pick_article(articles)
    script = generate_carousel_script(article)
    send_to_telegram(script, article)


async def cmd_buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /buscar [tema]  — busca noticias sobre ese tema y genera un carrusel.
    Ejemplo: /buscar instagram reels
    """
    tema = " ".join(context.args).strip() if context.args else ""
    if not tema:
        await update.message.reply_text(
            "Dime sobre qué quieres el carrusel.\n\n"
            "Ejemplos:\n"
            "/buscar instagram reels\n"
            "/buscar camara sony\n"
            "/buscar capcut\n"
            "/buscar iluminacion"
        )
        return

    await update.message.reply_text(f"🔍 Buscando noticias sobre *{tema}*...", parse_mode="Markdown")

    articles = scrape_all()
    tema_lower = tema.lower()
    matching = [
        a for a in articles
        if tema_lower in (a["title"] + " " + a.get("summary", "")).lower()
    ]

    if not matching:
        matching = [a for a in articles if is_relevant(a)]

    if not matching:
        await update.message.reply_text(
            f"No encontré noticias sobre *{tema}* en este momento.\n"
            "Intenta más tarde o prueba con otro término.",
            parse_mode="Markdown",
        )
        return

    article = random.choice(matching[:4])
    script = generate_carousel_script(article)
    send_to_telegram(script, article)


async def cmd_ahora(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/ahora — genera un carrusel con la noticia más reciente relevante."""
    await update.message.reply_text("⚡ Generando carrusel de última hora...")
    articles = scrape_all()
    if not articles:
        await update.message.reply_text("No encontré noticias ahora mismo. Intenta en unos minutos.")
        return
    article = pick_article(articles)
    script = generate_carousel_script(article)
    send_to_telegram(script, article)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 *Bot de Carruseles activo*\n\n"
        "Comandos disponibles:\n\n"
        "⚡ /ahora — última noticia relevante\n"
        "🔍 /buscar [tema] — noticia sobre un tema específico\n\n"
        "Ejemplos:\n"
        "/buscar instagram\n"
        "/buscar sony camera\n"
        "/buscar capcut update",
        parse_mode="Markdown",
    )


async def post_init(app: Application) -> None:
    # Start scheduler inside the running event loop
    scheduler = AsyncIOScheduler()
    for utc_hour in [11, 13, 15, 18, 21, 23]:
        scheduler.add_job(scheduled_post, "cron", hour=utc_hour, minute=0)
    scheduler.start()
    logger.info("Scheduler iniciado con 6 posts/día.")


def main():
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("ahora", cmd_ahora))
    app.add_handler(CommandHandler("buscar", cmd_buscar))

    logger.info("Bot iniciado — escuchando comandos y enviando posts programados.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
