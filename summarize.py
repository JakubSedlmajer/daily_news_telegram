#!/usr/bin/env python3
"""
Denní shrnutí zpráv z Blízkého východu → Telegram
"""

import os
import requests
import anthropic

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


def get_summary() -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        tools=[
            {
                "type": "web_search_20250305",
                "name": "web_search",
            }
        ],
        messages=[
            {
                "role": "user",
                "content": (
                    "Vyhledej aktuální zprávy z Blízkého východu za posledních 24 hodin. "
                    "Zaměř se na: Izrael/Gaza/Libanon, Írán, Sýrii, Irák, Jemen a případně Saúdskou Arábii ve spojitosti s bezpečností v Iráku a předně v Iráckém Kurdistánu. "
                    "Napiš stručné denní shrnutí v češtině. "
                    "Formát:\n"
                    "🌍 *Blízký východ – denní přehled*\n"
                    "_(datum)_\n\n"
                    "Pro každou relevantní zemi/téma použij emoji a krátký odstavec (2–3 věty). Nakonec shrnutí pro Irák a především Kurdistán"
                    "Na konci přidej 1 větu celkového hodnocení situace. "
                    "Používej Markdown formátování kompatibilní s Telegramem (tučné *text*, kurzíva _text_)."
                ),
            }
        ],
    )

    # Extrahuj textovou odpověď
    for block in response.content:
        if block.type == "text":
            return block.text

    return "Shrnutí se nepodařilo vygenerovat."


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
    print("Generuji shrnutí...")
    summary = get_summary()
    print(summary)
    send_telegram(summary)
