# 🚀 Stock Market Signal Bot

**Automated real-time signal scanner, tracker, and notifier for Borsa Istanbul (BIST) stocks.**

[![.NET](https://img.shields.io/badge/.NET-10.0-512BD4?style=flat-square&logo=dotnet)](https://dotnet.microsoft.com) [![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python)](https://python.org) [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat-square&logo=postgresql)](https://postgresql.org) [![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3-FF6600?style=flat-square&logo=rabbitmq)](https://rabbitmq.com)

---

## 📊 Features

| Feature | Description |
|---|---|
| **Trend Hunter** | RSI, MACD, ADX, SMA50/200, volume & momentum-based signal engine |
| **Smart Picks / Pro Engine** | Institutional tag system (Whale Volume, Smart Money, Falling Knife...) |
| **Unified Conviction** | Merges both engines into DIAMOND / GOLD / SILVER / BRONZE rating |
| **Signal History** | BUY/WATCH signals saved daily with T+1 / T+5 / T+21 performance tracking |
| **Telegram Notifications** | Smart cooldown-based alerts — no spam, no missed signals |
| **Excel Report** | Auto-updated color-coded Excel file after every analysis cycle |
| **Real-time Dashboard** | SignalR-powered live UI with Trend / Smart Picks / Portfolio tabs |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Python Worker                      │
│   TvDatafeed + YFinance → Trend Engine + Pro Engine  │
│   → Unified Score → RabbitMQ Publish                 │
│   → Telegram Notification (smart cooldown guard)    │
│   → Excel Export  (data/signal_history.xlsx)        │
└──────────────────────┬──────────────────────────────┘
                       │ AMQP
┌──────────────────────▼──────────────────────────────┐
│            C# .NET 10 API  (BorsaAPI)                │
│   RabbitMQ Consumer → PostgreSQL (hisseler table)   │
│   → SignalR Hub → Frontend                          │
│   → signal_history (daily-dedup insert)             │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP / WebSocket
┌──────────────────────▼──────────────────────────────┐
│                Web Interface (wwwroot)                │
│        Trend / Smart Picks / Portfolio / History     │
└─────────────────────────────────────────────────────┘
```

---

## ⚙️ Requirements

- **Docker & Docker Compose** (PostgreSQL + RabbitMQ)
- **.NET 10 SDK**
- **Python 3.10+**
- **Telegram Bot Token** (optional — for notifications)

---

## 🚀 Setup

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/StockMarketAppV2.git
cd StockMarketAppV2
```

### 2. Create Environment File

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
# PostgreSQL
DB_USER=postgres
DB_PASSWORD=your_strong_password
DB_NAME=borsa_db
DB_HOST=localhost
DB_PORT=5433

# RabbitMQ
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=your_strong_password
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672

# Telegram (optional)
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=987654321
```

### 3. Create `appsettings.json`

Create `BorsaAPI/appsettings.json`:

```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Host=localhost;Port=5433;Database=borsa_db;Username=postgres;Password=YOUR_PASSWORD"
  },
  "RabbitMQ": {
    "Host": "localhost",
    "Port": 5672,
    "Username": "guest",
    "Password": "YOUR_PASSWORD"
  },
  "Logging": {
    "LogLevel": { "Default": "Information" }
  }
}
```

### 4. Install Python Dependencies

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# or: source .venv/bin/activate  # Linux / Mac

pip install -r requirements.txt
```

### 5. Create `src/config.py`

```python
import os
from dotenv import load_dotenv
load_dotenv()

DB_AYARLARI = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     int(os.getenv("DB_PORT", 5433)),
    "dbname":   os.getenv("DB_NAME",     "borsa_db"),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

RABBITMQ_HOST     = os.getenv("RABBITMQ_HOST",     "localhost")
RABBITMQ_PORT     = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER     = os.getenv("RABBITMQ_USER",     "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID",   "")

HISSELER = [
    "AKBNK", "EREGL", "GARAN", "KOZAL", "SAHOL",
    "SDTTR", "THYAO", "TUPRS", "VAKBN", "YKBNK",
    # ... add all tickers here
]
```

### 6. Start Database & Message Broker

```bash
docker-compose up -d
```

PostgreSQL automatically runs all 3 migration files on first start:
- `001_create_hisseler.sql` — Main stocks table
- `002_add_unified_columns.sql` — Unified score columns
- `003_signal_history.sql` — Signal history table

### 7. Start the C# API

```bash
cd BorsaAPI
dotnet run
```

API runs at `http://localhost:5158`.

### 8. Start the Python Worker

```bash
python src/main.py
```

The worker scans all tickers continuously, applies both engines, and publishes results.

---

## 📱 Telegram Bot Setup

1. Message `@BotFather` on Telegram → send `/newbot`
2. Copy your bot token → paste into `.env`
3. Send any message to your new bot, then visit:
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
4. Find `chat.id` in the response → paste into `.env`

---

## � Telegram Notification Types

### 1. Trend Hunter Alert
Sent on BUY or STRONG_BUY signal:
```
🚀 STRONG_BUY — SDTTR

📊 Technical: RSI: 42.3 | ADX: 38.1 | Score: 85
💰 Price: 45.20 ₺
🎯 Target: 52.00 ₺  🛡️ Stop: 41.50 ₺
```

### 2. Smart Picks Alert
Sent on high Unified Score signals:
```
💎 DIAMOND — SDTTR

🏆 Unified Score: 100 | STRONG_BUY
🌍 Market Regime: BULL
🏷️ Tags: Strong Trend, Smart Money In, Long-Term Bull
```

### Smart Cooldown Rules

| Condition | Action |
|---|---|
| Signal escalated (e.g. BUY → STRONG_BUY) | Always notify |
| Score jumped ≥ 8 points | Notify after min 1 hour |
| STRONG_BUY continuing | Re-notify after 4 hours |
| BUY continuing | Re-notify after 6 hours |
| WATCH continuing | Re-notify after 8 hours |

---

## 📊 Excel Report

`data/sinyal_gecmisi.xlsx` is auto-regenerated at the end of every analysis cycle.

To generate manually:
```bash
python src/excel_exporter.py
```

**Sheet 1 — Signal History:**
- Symbol, Date, Signal type (color-coded rows: green = BUY, gold = WATCH)
- Conviction level (💎 DIAMOND / 🥇 GOLD / 🥈 SILVER / 🥉 BRONZE)
- Entry / Stop / Target price + Risk-Reward ratio
- RSI, ADX, MACD Histogram
- Market Regime, Strategy, Tags
- T+1 / T+5 / T+21 price and % performance (populated over time)

**Sheet 2 — Summary:**
- Total signal counts by type
- Average T+1 / T+5 / T+21 performance across all signals

---

## 🗂️ Project Structure

```
StockMarketAppV2/
├── BorsaAPI/               # C# .NET 10 Backend
│   ├── Controller/         # REST API endpoints
│   ├── Models/             # Hisse, SignalHistory models
│   ├── Services/           # HisseRepository, HisseService
│   ├── Hubs/               # SignalR BorsaHub
│   ├── Infrastructure/     # RabbitMQ Consumer
│   └── wwwroot/            # Frontend (HTML / JS / CSS)
├── src/                    # Python Worker
│   ├── main.py             # Main orchestration loop
│   ├── config.py           # Configuration (gitignored)
│   ├── excel_exporter.py   # Excel report generator
│   └── core/
│       ├── analiz.py             # Data fetcher (TvDatafeed / YFinance)
│       ├── trend_engine.py       # Trend Hunter signal engine
│       ├── pro_engine.py         # Pro / Institutional analysis engine
│       ├── telegram_notifier.py  # Telegram alert sender
│       ├── notification_guard.py # Smart cooldown / dedup system
│       └── rabbitmq_manager.py   # RabbitMQ connection manager
├── migrations/             # PostgreSQL SQL migration files
├── data/                   # Generated data (gitignored)
│   └── sinyal_gecmisi.xlsx
├── docker-compose.yml      # PostgreSQL + RabbitMQ services
├── requirements.txt        # Python dependencies
└── .env.example            # Environment variable template
```

---

## 🔌 API Endpoints

| Method | URL | Description |
|---|---|---|
| GET | `/api/hisseler` | All stock data |
| GET | `/api/hisseler?onlyTrend=true` | BUY / STRONG_BUY signals only |
| GET | `/api/market/pro` | Smart Picks / Pro Engine data |
| GET | `/api/signals/history?limit=50&sembol=THYAO` | Signal history (filterable) |
| WS  | `/borsahub` | SignalR real-time updates |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | C# .NET 10, ASP.NET Core, SignalR |
| **Analysis Engine** | Python 3.10, Pandas, Pandas-TA |
| **Data Sources** | TvDatafeed (TradingView), Yahoo Finance |
| **Messaging** | RabbitMQ (AMQP) via Pika / .NET client |
| **Database** | PostgreSQL 15 |
| **Frontend** | HTML5, Vanilla JS, Tailwind CSS |
| **Notifications** | Telegram Bot API |
| **Reporting** | OpenPyXL (Excel) |
| **Infrastructure** | Docker, Docker Compose |

---

## ⚠️ Disclaimer

This project is for **educational and research purposes only**. It does not constitute financial advice. Always do your own research before making investment decisions. TvDatafeed is a free data source and may have limitations in data quality or availability.

---

## 📄 License

Personal use only.
