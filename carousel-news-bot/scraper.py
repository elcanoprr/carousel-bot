import requests
from bs4 import BeautifulSoup
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}


def fetch(url: str) -> Optional[BeautifulSoup]:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return None


def _clean(text: str) -> str:
    return " ".join(text.split()).strip()


def _rss(url: str, source: str, topic: str, limit: int = 4) -> List[Dict]:
    """Generic RSS/Atom feed scraper."""
    soup = fetch(url)
    if not soup:
        return []
    articles = []
    for item in soup.find_all(["item", "entry"])[:limit * 2]:
        title_el = item.find("title")
        link_el = item.find("link")
        desc_el = item.find("description") or item.find("summary") or item.find("content")
        if not title_el:
            continue
        title = _clean(title_el.get_text())
        if len(title) < 10:
            continue
        href = (_clean(link_el.get_text()) if link_el and link_el.get_text().strip()
                else link_el.get("href", "") if link_el else "")
        raw = desc_el.get_text() if desc_el else ""
        summary = _clean(BeautifulSoup(raw, "html.parser").get_text())[:300]
        articles.append({"title": title, "url": href, "summary": summary,
                         "source": source, "topic": topic})
        if len(articles) >= limit:
            break
    return articles


def _html(url: str, source: str, topic: str, base: str = "", limit: int = 4) -> List[Dict]:
    """Generic HTML article scraper."""
    soup = fetch(url)
    if not soup:
        return []
    articles = []
    seen = set()
    for el in soup.find_all(["article", "div"])[:60]:
        title_el = el.find(["h1", "h2", "h3", "h4"])
        link_el = el.find("a", href=True)
        summary_el = el.find("p")
        if not title_el:
            continue
        title = _clean(title_el.get_text())
        if len(title) < 20 or title in seen:
            continue
        seen.add(title)
        href = link_el["href"] if link_el else ""
        if href and not href.startswith("http") and base:
            href = base + href
        articles.append({
            "title": title,
            "url": href,
            "summary": _clean(summary_el.get_text())[:300] if summary_el else "",
            "source": source,
            "topic": topic,
        })
        if len(articles) >= limit:
            break
    return articles


# ─── Redes Sociales y Marketing Digital ───────────────────────────────────────

def scrape_socialmediatoday() -> List[Dict]:
    return _html("https://www.socialmediatoday.com",
                 "Social Media Today", "redes sociales",
                 base="https://www.socialmediatoday.com")


def scrape_marketing4ecommerce() -> List[Dict]:
    # WordPress site — try RSS first
    arts = _rss("https://marketing4ecommerce.net/feed/", "Marketing4eCommerce", "redes sociales")
    return arts or _html("https://marketing4ecommerce.net", "Marketing4eCommerce", "redes sociales",
                         base="https://marketing4ecommerce.net")


def scrape_puromarketing() -> List[Dict]:
    soup = fetch("https://www.puromarketing.com")
    if not soup:
        return []
    articles = []
    seen = set()
    for link_el in soup.find_all("a", href=lambda h: h and "puromarketing.com/" in h)[:40]:
        title_el = link_el.find(["h2", "h3", "h4", "span", "p"])
        title = _clean(title_el.get_text() if title_el else link_el.get_text())
        if len(title) < 20 or title in seen:
            continue
        seen.add(title)
        articles.append({
            "title": title,
            "url": link_el["href"],
            "summary": "",
            "source": "Puro Marketing",
            "topic": "redes sociales",
        })
        if len(articles) >= 4:
            break
    return articles


# ─── Inteligencia Artificial ──────────────────────────────────────────────────

def scrape_therundown() -> List[Dict]:
    soup = fetch("https://www.therundown.ai/")
    if not soup:
        return []
    articles = []
    seen = set()
    for link_el in soup.find_all("a", href=lambda h: h and "/p/" in h):
        title = _clean(link_el.get_text()).split("PLUS:")[0].strip()
        if len(title) < 20 or title in seen:
            continue
        seen.add(title)
        href = link_el["href"]
        if not href.startswith("http"):
            href = "https://www.therundown.ai" + href
        articles.append({"title": title, "url": href, "summary": "",
                         "source": "The Rundown AI", "topic": "inteligencia artificial"})
        if len(articles) >= 4:
            break
    return articles


def scrape_thedecoder() -> List[Dict]:
    arts = _rss("https://the-decoder.com/feed/", "The Decoder", "inteligencia artificial")
    return arts or _html("https://the-decoder.com", "The Decoder", "inteligencia artificial",
                         base="https://the-decoder.com")


def scrape_timesofai() -> List[Dict]:
    # timesofai.com has outdated SSL — skip silently
    return []


# ─── Creación de Contenido y Creator Economy ──────────────────────────────────

def scrape_tubefilter() -> List[Dict]:
    return _rss("http://feeds.feedburner.com/tubefilterNews", "Tubefilter", "creación de contenido")


def scrape_passionfroot() -> List[Dict]:
    soup = fetch("https://www.passionfroot.me/blog")
    if not soup:
        return []
    articles = []
    seen = set()
    for link_el in soup.find_all("a", href=lambda h: h and "/blog/" in h and len(h) > 10)[:20]:
        title_el = link_el.find(["h2", "h3", "h4", "p", "span"])
        raw = title_el.get_text() if title_el else link_el.get_text()
        # Strip "Month Day, Year•Nmin read" prefix
        import re
        title = re.sub(r"^[\w]+ \d+, \d{4}•\d+min read", "", _clean(raw)).strip()
        if len(title) < 20 or title in seen:
            continue
        seen.add(title)
        href = link_el["href"]
        if not href.startswith("http"):
            href = "https://www.passionfroot.me" + href
        articles.append({
            "title": title,
            "url": href,
            "summary": "",
            "source": "Passionfroot",
            "topic": "creación de contenido",
        })
        if len(articles) >= 4:
            break
    return articles


# ─── Cámaras, Hardware y Equipos ──────────────────────────────────────────────

def scrape_cined() -> List[Dict]:
    arts = _rss("https://www.cined.com/feed/", "CineD", "cámaras y producción")
    return arts or _html("https://www.cined.com", "CineD", "cámaras y producción",
                         base="https://www.cined.com")


def scrape_newsshooter() -> List[Dict]:
    arts = _rss("https://www.newsshooter.com/feed/", "Newsshooter", "cámaras y producción")
    return arts or _html("https://www.newsshooter.com", "Newsshooter", "cámaras y producción",
                         base="https://www.newsshooter.com")


# ─── Lanzamientos de Software ─────────────────────────────────────────────────

def scrape_producthunt() -> List[Dict]:
    return _rss("https://www.producthunt.com/feed", "Product Hunt", "tecnología e IA")


# ─── Fuentes Oficiales ────────────────────────────────────────────────────────

def scrape_openai_news() -> List[Dict]:
    soup = fetch("https://openai.com/news/")
    if not soup:
        return []
    articles = []
    seen = set()
    for link_el in soup.find_all("a", href=lambda h: h and h.startswith("/"))[:30]:
        title_el = link_el.find(["h2", "h3", "h4", "p", "span"])
        if not title_el:
            continue
        title = _clean(title_el.get_text())
        if len(title) < 20 or title in seen:
            continue
        seen.add(title)
        articles.append({
            "title": title,
            "url": "https://openai.com" + link_el["href"],
            "summary": "",
            "source": "OpenAI News",
            "topic": "inteligencia artificial",
        })
        if len(articles) >= 4:
            break
    return articles


def scrape_meta_news() -> List[Dict]:
    arts = _rss("https://about.fb.com/feed/", "Meta Newsroom", "redes sociales")
    return arts or _html("https://about.fb.com/news/", "Meta Newsroom", "redes sociales",
                         base="https://about.fb.com")


def scrape_tiktok_newsroom() -> List[Dict]:
    arts = _rss("https://newsroom.tiktok.com/en-us/rss", "TikTok Newsroom", "redes sociales")
    return arts or _html("https://newsroom.tiktok.com/en-us/", "TikTok Newsroom", "redes sociales",
                         base="https://newsroom.tiktok.com")


# ─── Orquestador ──────────────────────────────────────────────────────────────

def scrape_all() -> List[Dict]:
    scrapers = [
        # Redes sociales
        scrape_socialmediatoday,
        scrape_marketing4ecommerce,
        scrape_puromarketing,
        # IA
        scrape_therundown,
        scrape_thedecoder,
        scrape_timesofai,
        # Contenido
        scrape_tubefilter,
        scrape_passionfroot,
        # Hardware
        scrape_cined,
        scrape_newsshooter,
        # Lanzamientos
        scrape_producthunt,
        # Fuentes oficiales
        scrape_openai_news,
        scrape_meta_news,
        scrape_tiktok_newsroom,
    ]
    all_articles = []
    for scraper in scrapers:
        try:
            results = scraper()
            all_articles.extend(results)
            logger.info(f"{scraper.__name__}: {len(results)} artículos")
        except Exception as e:
            logger.error(f"Error en {scraper.__name__}: {e}")
    return all_articles
