#!/usr/bin/env python3
"""
Denní shrnutí zpráv z Blízkého východu → Telegram
Web search: Claude (max 3 searche = ~$0.03/den)
"""

import os
import requests
import anthropic

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

PROMPT = (
    "Vyhledej aktuální zprávy z Blízkého východu za posledních 24 hodin. "
    "Zaměř se na: Izrael/Gaza/Libanon, Írán, Sýrii, Irák a Jemen. Udělej shrnutí bezpečnosti ve spojitosti s Irákem a Kurdistánem. "
    "Napiš stručné denní shrnutí v češtině.\n\n"
    "Formát:\n"
    "🌍 *Blízký východ – denní přehled*\n"
    "_(dnešní datum)_\n\n"
    "Pro každou relevantní zemi použij emoji a napiš 2–3 věty. "
    "Používej Markdown kompatibilní s Telegramem (*tučné*, _kurzíva_). "
    "Na konci přidej jednu větu celkového hodnocení situace."
)


def get_summary() -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    messages = [{"role": "user", "content": PROMPT}]
    tools = [{
        "type": "web_search_20250305",
        "name": "web_search",
        "max_uses": 3,
    }]

    # Agentic loop
    while True:
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            tools=tools,
            messages=messages,
        )

        print(f"stop_reason: {response.stop_reason}")
        print(f"block types: {[b.type for b in response.content]}")

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            for block in reversed(response.content):
                if hasattr(block, "text"):
                    return block.text
            return "Shrnutí se nepodařilo vygenerovat."

        # Zpracuj tool_use bloky
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": "OK",
                })

        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        else:
            for block in reversed(response.content):
                if hasattr(block, "text"):
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
