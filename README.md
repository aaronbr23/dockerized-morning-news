# dockerized-morning-news

A Dockerized financial news reporter designed to run on a Raspberry Pi. Every morning, Gemini AI searches for the latest news and analyzes their potential impact on your portfolio — delivering a concise report straight to your Telegram.

## How it works

1. A cronjob triggers the Docker container every morning at 06:30
2. Gemini AI searches for recent news relevant to your configured assets
3. For each relevant news item, it evaluates whether the impact is positive, negative, or unclear
4. The report is sent to your Telegram chat

## Stack

Python · Google Gemini 2.5 Flash · python-telegram-bot · Docker

## Setup

### 1. Prerequisites

- A Raspberry Pi with Docker and Docker Compose installed
- A [Google AI Studio](https://aistudio.google.com/apikey) account (free)
- A Telegram bot created via [@BotFather](https://t.me/BotFather)

### 2. Clone the repository

```bash
git clone https://github.com/aaronbr23/dockerized-morning-news.git
cd dockerized-morning-news
```

### 3. Configure your environment

Rename `change.env` to `.env` and fill in your credentials:

```bash
mv change.env .env
nano .env
```

```env
GEMINI_API_KEY=your_gemini_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

To get your Telegram chat ID, send a message to your bot and open:
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
```
Look for `"chat":{"id":...}` in the response.

### 4. Configure your assets

Edit `config.yml` to add or remove assets by ISIN:

```yaml
assets:
  - isin: IE00B4L5Y983
    name: MSCI World (iShares Core)
    type: etf

  - isin: DE0007164600
    name: SAP
    type: stock
```

Both `etf` and `stock` are supported as types.

### 5. Test it

```bash
docker compose up --build
```

If the Telegram message arrives, everything is working.

### 6. Schedule the daily report

Open the crontab on your Raspberry Pi:

```bash
crontab -e
```

Add this line to run the report every morning at 06:30:

```
30 6 * * * cd /home/pi/dockerized-morning-news && docker compose up --build >> /var/log/market-reporter.log 2>&1
```

## Project structure

```
dockerized-morning-news/
├── config.yml        # Add your assets here (ISIN, name, type)
├── reporter.py       # Main script
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── change.env        # Rename to .env and fill in your keys
└── .gitignore
```