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

PROMPT = (
    "Vyhledej aktuální zprávy z Blízkého východu za posledních 24 hodin. "
    "Zaměř se na: Izrael/Gaza/Libanon, Írán, Sýrii, Irák, Jemen a případně Saúdskou Arábii. "
    "Napiš stručné denní shrnutí v češtině. "
    "Formát:\n"
    "🌍 *Blízký východ – denní přehled*\n"
    "_(datum)_\n\n"
    "Pro každou relevantní zemi/téma použij emoji a krátký odstavec (2–3 věty). "
    "Na konci přidej 1 větu celkového hodnocení situace. "
    "Používej Markdown formátování kompatibilní s Telegramem (tučné *text*, kurzíva _text_)."
)


def get_summary() -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    messages = [{"role": "user", "content": PROMPT}]
    tools = [{"type": "web_search_20250305", "name": "web_search"}]

    # Agentic loop
    while True:
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=2048,
            tools=tools,
            messages=messages,
        )

        print(f"stop_reason: {response.stop_reason}")
        print(f"block types: {[b.type for b in response.content]}")

        # Sbírej všechny textové bloky
        text_blocks = [b.text for b in response.content if hasattr(b, "text") and b.text]

        if response.stop_reason == "end_turn":
            if text_blocks:
                return "\n\n".join(text_blocks)
            return "Shrnutí se nepodařilo vygenerovat."

        # Přidej odpověď do historie
        messages.append({"role": "assistant", "content": response.content})

        # Zpracuj tool_use bloky
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": "Proveď vyhledávání a zahrň výsledky do shrnutí.",
                })

        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        else:
            # Žádné tool cally ale ani end_turn → vrať co máme
            if text_blocks:
                return "\n\n".join(text_blocks)
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
