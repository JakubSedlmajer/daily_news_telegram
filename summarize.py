#!/usr/bin/env python3
"""
Denní shrnutí zpráv z Blízkého východu → Telegram
Zdroj zpráv: NewsAPI (zdarma)
Shrnutí: Claude Haiku (levné)
"""

import os
import requests
import anthropic
from datetime import datetime, timedelta, timezone

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
NEWSAPI_KEY = os.environ["NEWSAPI_KEY"]

TOPICS = [
    "Israel Gaza",
    "Iran Israel",
    "Syria",
    "Iraq war",
    "Yemen Houthi",
    "Lebanon Hezbollah",
    "Middle East",
]


def fetch_news() -> str:
    """Stáhne zprávy z NewsAPI za posledních 24 hodin."""
    yesterday = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    all_articles = []

    for topic in TOPICS:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": topic,
            "from": yesterday,
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": 3,
            "apiKey": NEWSAPI_KEY,
        }
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code != 200:
            print(f"NewsAPI chyba pro '{topic}': {resp.status_code}")
            continue

        data = resp.json()
        articles = data.get("articles", [])
        for a in articles:
            title = a.get("title", "")
            description = a.get("description", "")
            source = a.get("source", {}).get("name", "")
            published = a.get("publishedAt", "")[:10]
            if title and "[Removed]" not in title:
                all_articles.append(f"[{published}] {source}: {title}. {description}")

    if not all_articles:
        return "Žádné zprávy nenalezeny."

    # Odstraň duplicity
    seen = set()
    unique = []
    for a in all_articles:
        if a not in seen:
            seen.add(a)
            unique.append(a)

    return "\n".join(unique[:30])  # max 30 článků


def get_summary(news_text: str) -> str:
    """Shrne zprávy pomocí Claude Haiku."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    today = datetime.now().strftime("%-d. %-m. %Y")

    prompt = f"""Na základě těchto zpravodajských článků z posledních 24 hodin napiš stručné denní shrnutí situace na Blízkém východě v češtině.

ČLÁNKY:
{news_text}

FORMÁT (použij přesně tento):
🌍 *Blízký východ – denní přehled*
_{today}_

Pro každou relevantní zemi/téma použij emoji a napiš 2–3 věty. Používej Markdown kompatibilní s Telegramem (*tučné*, _kurzíva_). Na konci přidej jednu větu celkového hodnocení situace.

Piš pouze na základě poskytnutých článků, nevymýšlej informace."""

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text


def send_telegram(text: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    print("Zpráva odeslána do Telegramu.")


if __name__ == "__main__":
    print("Stahuji zprávy z NewsAPI...")
    news = fetch_news()
    print(f"Nalezeno článků: {news.count(chr(10)) + 1}")

    print("Generuji shrnutí (Claude Haiku)...")
    summary = get_summary(news)
    print(summary)

    send_telegram(summary)
