#!/usr/bin/env python3
"""
Denní shrnutí zpráv z Blízkého východu → Telegram
Zdroj zpráv: NewsAPI (zdarma)
Shrnutí: Claude Haiku (levné)
"""

import os
import requests
import anthropic
from datetime import datetime

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
NEWSAPI_KEY = os.environ["NEWSAPI_KEY"]

TOPICS = [
    "Israel Gaza war",
    "Iran Israel attack",
    "Syria conflict",
    "Iraq militia",
    "Yemen Houthi",
    "Lebanon Hezbollah",
    "Middle East news",
]


def fetch_news() -> str:
    """Stáhne nejnovější zprávy z NewsAPI."""
    all_articles = []

    for topic in TOPICS:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": topic,
            "sortBy": "publishedAt",  # nejnovější první
            "language": "en",
            "pageSize": 5,
            "apiKey": NEWSAPI_KEY,
        }
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code != 200:
            print(f"NewsAPI chyba pro '{topic}': {resp.status_code} {resp.text}")
            continue

        data = resp.json()
        articles = data.get("articles", [])
        for a in articles:
            title = a.get("title", "")
            description = a.get("description", "") or ""
            source = a.get("source", {}).get("name", "")
            published = a.get("publishedAt", "")[:10]
            if title and "[Removed]" not in title:
                all_articles.append(
                    f"[{published}] {source}: {title}. {description[:200]}"
                )

    if not all_articles:
        return "Žádné zprávy nenalezeny."

    # Odstraň duplicity a seřaď podle data (nejnovější první)
    seen = set()
    unique = []
    for a in sorted(all_articles, reverse=True):
        if a not in seen:
            seen.add(a)
            unique.append(a)

    return "\n".join(unique[:40])


def get_summary(news_text: str) -> str:
    """Shrne zprávy pomocí Claude Haiku."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    today = datetime.now().strftime("%-d. %-m. %Y")

    prompt = f"""Na základě těchto zpravodajských článků napiš stručné denní shrnutí situace na Blízkém východě v češtině.

ČLÁNKY:
{news_text}

FORMÁT (použij přesně tento):
🌍 *Blízký východ – denní přehled*
_{today}_

Pro každou relevantní zemi/téma použij emoji a napiš 2–3 věty. Používej Markdown kompatibilní s Telegramem (*tučné*, _kurzíva_). Na konci přidej jednu větu celkového hodnocení situace.

Piš pouze na základě poskytnutých článků, nevymýšlej informace. Pokud jsou články starší, uveď datum u každé sekce."""

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
    print(f"Články:\n{news[:500]}...")

    print("\nGeneruji shrnutí (Claude Haiku)...")
    summary = get_summary(news)
    print(summary)

    send_telegram(summary)
