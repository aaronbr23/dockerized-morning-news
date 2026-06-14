import os
import asyncio
from datetime import date
import yaml
from google import genai
from google.genai import types
from telegram import Bot

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def load_config():
    with open("config.yml", "r") as f:
        return yaml.safe_load(f)

def build_prompt(assets, language):
    if language == "en":
        asset_list = ""
        for asset in assets:
            type_label = "ETF" if asset["type"] == "etf" else "Stock"
            asset_list += f"- {asset['name']} ({type_label}, ISIN: {asset['isin']})\n"

        return f"""
You are a precise financial analyst. Today is {date.today().strftime('%B %d, %Y')}.

Search for recent news from the last 24 hours that could impact the following assets:
{asset_list}
For each relevant news item:
- Briefly describe the news
- Explain which assets are affected
- Assess the impact: positive, negative, or unclear

Focus on: macroeconomics, interest rate decisions, geopolitics, company news, technology sector.
Ignore unimportant or irrelevant news.
Format: One block per news item with bullet points. Maximum 5 news items.
Write ONLY the report, no introduction or closing remarks. Do not use emojis.
"""
    else:
        asset_list = ""
        for asset in assets:
            type_label = "ETF" if asset["type"] == "etf" else "Aktie"
            asset_list += f"- {asset['name']} ({type_label}, ISIN: {asset['isin']})\n"

        return f"""
Du bist ein präziser Finanzanalyst. Heute ist der {date.today().strftime('%d.%m.%Y')}.

Suche nach aktuellen Nachrichten der letzten 24 Stunden, die Auswirkungen auf folgende Assets haben könnten:
{asset_list}
Für jede relevante Nachricht:
- Beschreibe kurz die Nachricht
- Erkläre welche Assets davon betroffen sind
- Bewerte die Auswirkung: positiv, negativ oder unklar

Fokus auf: Makroökonomie, Zinsentscheide, Geopolitik, Unternehmensnews, Technologiesektor.
Ignoriere unwichtige oder nicht relevante Nachrichten.
Format: Pro Nachricht ein Block mit Bullet Points. Maximal 5 Nachrichten.
Schreibe NUR den Bericht, keine Einleitung oder Abschluss. Verwende keine Emojis.
Der Bericht darf maximal 3950 Zeichen lang sein.
"""

async def main():
    config = load_config()
    assets = config["assets"]
    language = config.get("language", "de")
    prompt = build_prompt(assets, language)

    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    )
    report = response.text

    today = date.today().strftime('%d.%m.%Y')
    title = "Market Report" if language == "en" else "Marktbericht"
    message = f"*{title} {today}*\n\n{report}"

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=message,
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    asyncio.run(main())