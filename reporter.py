import os
import asyncio
from datetime import date
import yaml
import google.generativeai as genai
from telegram import Bot

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def load_config():
    with open("config.yml", "r") as f:
        return yaml.safe_load(f)

def build_prompt(assets):
    asset_list = ""
    for asset in assets:
        type_label = "ETF" if asset["type"] == "etf" else "Aktie"
        asset_list += f"- {asset['name']} ({type_label}, ISIN: {asset['isin']})\n"

    return f"""
Du bist ein präziser Finanzanalyst. Heute ist der {date.today().strftime('%d.%m.%Y')}.

Schreibe einen kurzen Morgenbericht (~150 Wörter) auf Deutsch mit Bullet Points über diese Finanzprodukte:
{asset_list}
Für jedes Produkt:
- Aktueller Kurs und Veränderung zum Vortag (in % und absolut)
- 2-3 relevante Nachrichten oder Ereignisse der letzten 24h die den Kurs beeinflusst haben

Nutze aktuelle Daten aus dem Internet.
Format: Kurze Überschrift pro Produkt, darunter Bullet Points.
Schreibe NUR den Bericht, keine Einleitung oder Abschluss.
"""

async def main():
    config = load_config()
    assets = config["assets"]
    prompt = build_prompt(assets)

    # Gemini aufrufen
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        tools="google_search"  # Grounding mit Google Search für aktuelle Daten
    )
    response = model.generate_content(prompt)
    report = response.text

    # Telegram senden
    today = date.today().strftime('%d.%m.%Y')
    message = f"📊 *Marktbericht {today}*\n\n{report}"

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=message,
        parse_mode="Markdown"
    )
    print(f"✅ Bericht erfolgreich gesendet ({len(report)} Zeichen)")

if __name__ == "__main__":
    asyncio.run(main())
