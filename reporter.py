import os
import asyncio
import html
import re
from datetime import date
import yaml
from google import genai
from google.genai import types
from telegram import Bot

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

TELEGRAM_MAX_LENGTH = 4096

def load_config():
    with open("config.yml", "r") as f:
        return yaml.safe_load(f)

def build_prompt_single(asset, language):
    if language == "en":
        type_label = "ETF" if asset["type"] == "etf" else "Stock"
        asset_line = f"- {asset['name']} ({type_label}, ISIN: {asset['isin']})"
        return f"""
You are a precise financial analyst. Today is {date.today().strftime('%B %d, %Y')}.

Search for recent news from the last 24 hours that could impact the following asset:
{asset_line}

For each relevant news item:
- Briefly describe the news
- Explain how this asset is affected
- Assess the impact: positive, negative, or unclear

Focus on: macroeconomics, interest rate decisions, geopolitics, company news, technology sector.
Ignore unimportant or irrelevant news.
Format: One block per news item, separated by a blank line. Start each block with a short headline, followed by "•" bullet points. Maximum 3 news items.
Write ONLY the report, no introduction or closing remarks. Do not use emojis.
Do not use any Markdown formatting (no asterisks, hashes, or underscores) and no HTML tags.
The text should not be longer than 3500 characters. Make sure the report ends with a complete sentence.
"""
    else:
        type_label = "ETF" if asset["type"] == "etf" else "Aktie"
        asset_line = f"- {asset['name']} ({type_label}, ISIN: {asset['isin']})"
        return f"""
Du bist ein präziser Finanzanalyst. Heute ist der {date.today().strftime('%d.%m.%Y')}.

Suche nach aktuellen Nachrichten der letzten 24 Stunden, die Auswirkungen auf folgendes Asset haben könnten:
{asset_line}

Für jede relevante Nachricht:
- Beschreibe kurz die Nachricht
- Erkläre wie dieses Asset davon betroffen ist
- Bewerte die Auswirkung: positiv, negativ oder unklar

Fokus auf: Makroökonomie, Zinsentscheide, Geopolitik, Unternehmensnews, Technologiesektor.
Ignoriere unwichtige oder nicht relevante Nachrichten.
Format: Pro Nachricht ein Block, getrennt durch eine Leerzeile. Beginne jeden Block mit einer kurzen Überschrift, gefolgt von "•" Bullet Points. Maximal 3 Nachrichten.
Schreibe NUR den Bericht, keine Einleitung oder Abschluss. Verwende keine Emojis.
Verwende kein Markdown (keine Sternchen, Rauten oder Unterstriche) und kein HTML.
Der Text darf maximal 3500 Zeichen lang sein. Achte darauf, dass der Bericht mit einem vollständigen Satz endet.
"""

async def main():
    config = load_config()
    assets = config["assets"]
    language = config.get("language", "de")

    client = genai.Client(api_key=GEMINI_API_KEY)
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    today = date.today().strftime('%d.%m.%Y')

    for asset in assets:
        prompt = build_prompt_single(asset, language)
        type_label = ("ETF" if asset["type"] == "etf" else ("Stock" if language == "en" else "Aktie"))
        header = f"<b>{html.escape(asset['name'])} ({type_label}) – {today}</b>\n\n"

        report = None
        last_error = None
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())]
                    )
                )
                report = response.text
                break
            except Exception as e:
                last_error = e
                if attempt < 2:
                    await asyncio.sleep(5 * (attempt + 1))

        if report is None:
            error_text = "No report available." if language == "en" else "Kein Bericht verfügbar."
            report = f"{error_text}\n\n({last_error})"

        message = header + html.escape(report.strip())

        if len(message) > TELEGRAM_MAX_LENGTH:
            cutoff = TELEGRAM_MAX_LENGTH - 3
            message = message[:cutoff]
            # avoid cutting an HTML entity in half (e.g. "&amp" without ";")
            message = re.sub(r"&[a-zA-Z0-9#]*$", "", message)
            message += "..."

        try:
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message,
                parse_mode="HTML",
            )
        except Exception as e:
            print(f"Failed to send Telegram message for {asset['name']}: {e}")

        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())