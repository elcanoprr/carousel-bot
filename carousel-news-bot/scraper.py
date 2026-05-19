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


def scrape_socialmediatoday() -> List[Dict]:
    soup = fetch("https://www.socialmediatoday.com")
    if not soup:
        return []
    articles = []
    seen = set()
    for el in soup.find_all(["article", "div"])[:40]:
        title_el = el.find(["h2", "h3", "h4"])
        link_el = el.find("a", href=True)
        summary_el = el.find("p")
        if not title_el:
            continue
        title = _clean(title_el.get_text())
        if len(title) < 20 or title in seen:
            continue
        seen.add(title)
        href = link_el["href"] if link_el else ""
        if href and not href.startswith("http"):
            href = "https://www.socialmediatoday.com" + href
        articles.append({
            "title": title,
            "url": href,
            "summary": _clean(summary_el.get_text())[:300] if summary_el else "",
            "source": "Social Media Today",
            "topic": "redes sociales",
        })
    return articles[:4]


def scrape_therundown() -> List[Dict]:
    # Articles are at /p/<slug> — find those links on the homepage
    soup = fetch("https://www.therundown.ai/")
    if not soup:
        return []
    articles = []
    seen = set()
    for link_el in soup.find_all("a", href=lambda h: h and "/p/" in h):
        title = _clean(link_el.get_text())
        # Titles often have "PLUS: ..." appended — keep only the main headline
        title = title.split("PLUS:")[0].strip()
        if len(title) < 20 or title in seen:
            continue
        seen.add(title)
        href = link_el["href"]
        if not href.startswith("http"):
            href = "https://www.therundown.ai" + href
        articles.append({
            "title": title,
            "url": href,
            "summary": "",
            "source": "The Rundown AI",
            "topic": "inteligencia artificial",
        })
        if len(articles) >= 4:
            break
    return articles


def scrape_tubefilter() -> List[Dict]:
    # Use RSS feed — cleaner than scraping the JS-heavy homepage
    soup = fetch("http://feeds.feedburner.com/tubefilterNews")
    if not soup:
        return []
    articles = []
    for item in soup.find_all("item")[:6]:
        title_el = item.find("title")
        link_el = item.find("link")
        desc_el = item.find("description")
        if not title_el:
            continue
        title = _clean(title_el.get_text())
        if len(title) < 20:
            continue
        href = _clean(link_el.get_text()) if link_el else ""
        raw_desc = desc_el.get_text() if desc_el else ""
        summary = _clean(BeautifulSoup(raw_desc, "html.parser").get_text())[:300]
        articles.append({
            "title": title,
            "url": href,
            "summary": summary,
            "source": "Tubefilter",
            "topic": "creación de contenido",
        })
    return articles[:4]


def scrape_cined() -> List[Dict]:
    soup = fetch("https://www.cined.com")
    if not soup:
        return []
    articles = []
    seen = set()
    for el in soup.find_all(["article", "div"])[:40]:
        title_el = el.find(["h2", "h3"])
        link_el = el.find("a", href=True)
        summary_el = el.find("p")
        if not title_el:
            continue
        title = _clean(title_el.get_text())
        if len(title) < 20 or title in seen:
            continue
        seen.add(title)
        href = link_el["href"] if link_el else ""
        if href and not href.startswith("http"):
            href = "https://www.cined.com" + href
        articles.append({
            "title": title,
            "url": href,
            "summary": _clean(summary_el.get_text())[:300] if summary_el else "",
            "source": "CineD",
            "topic": "creación de contenido",
        })
    return articles[:4]


def scrape_producthunt() -> List[Dict]:
    # Use Atom RSS feed — ProductHunt blocks direct scraping
    soup = fetch("https://www.producthunt.com/feed")
    if not soup:
        return []
    articles = []
    for entry in soup.find_all("entry")[:6]:
        title_el = entry.find("title")
        link_el = entry.find("link")
        content_el = entry.find("content") or entry.find("summary")
        if not title_el:
            continue
        title = _clean(title_el.get_text())
        if len(title) < 5:
            continue
        href = link_el.get("href", "") if link_el else ""
        raw_content = content_el.get_text() if content_el else ""
        summary = _clean(BeautifulSoup(raw_content, "html.parser").get_text())[:300]
        articles.append({
            "title": title,
            "url": href,
            "summary": summary,
            "source": "Product Hunt",
            "topic": "tecnología e IA",
        })
    return articles[:4]


def scrape_all() -> List[Dict]:
    scrapers = [
        scrape_socialmediatoday,
        scrape_therundown,
        scrape_tubefilter,
        scrape_cined,
        scrape_producthunt,
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
