# 🚀 Stock Market Signal Bot

**Borsa İstanbul hisselerini gerçek zamanlı tarayan, sinyal üreten ve takip eden otomatik analiz sistemi.**

[![.NET](https://img.shields.io/badge/.NET-8.0-512BD4?style=flat-square&logo=dotnet)](https://dotnet.microsoft.com) [![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python)](https://python.org) [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat-square&logo=postgresql)](https://postgresql.org) [![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3-FF6600?style=flat-square&logo=rabbitmq)](https://rabbitmq.com)

---

## 📊 Neler Yapıyor?

| Özellik | Açıklama |
|---|---|
| **Trend Hunter** | RSI, MACD, ADX, SMA50/200, hacim ve momentum bazlı sinyal motoru |
| **Smart Picks / Pro Engine** | Kurumsal etiket sistemi (Whale Volume, Smart Money, Falling Knife...) |
| **Unified Conviction** | İki motoru birleştiren DIAMOND / GOLD / SILVER / BRONZE skoru |
| **Signal History** | Her BUY/WATCH sinyali günlük olarak kaydedilir, T+1/T+5/T+21 takibi |
| **Telegram Bildirimleri** | Sinyal yükseltmesi veya cooldown'a göre akıllı bildirim gönderimi |
| **Excel Raporu** | Her döngüde otomatik güncellenen renkli Excel dosyası |
| **Gerçek Zamanlı UI** | SignalR tabanlı canlı dashboard (Trend / Smart Picks / Portföy sekmeleri) |

---

## 🏗️ Mimari

```
┌─────────────────────────────────────────────────────┐
│                   Python Worker                      │
│   TvDatafeed + YFinance → Trend Engine + Pro Engine  │
│   → Unified Score → RabbitMQ Publish                 │
│   → Telegram Notification (smart cooldown)          │
│   → Excel Export (data/sinyal_gecmisi.xlsx)         │
└──────────────────────┬──────────────────────────────┘
                       │ AMQP
┌──────────────────────▼──────────────────────────────┐
│              C# .NET 8 API (BorsaAPI)                │
│   RabbitMQ Consumer → PostgreSQL (hisseler tablosu) │
│   → SignalR Hub → Frontend                          │
│   → signal_history (günlük dedup ile kayıt)        │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP / WebSocket
┌──────────────────────▼──────────────────────────────┐
│               Web Arayüzü (wwwroot)                  │
│   Trend / Smart Picks / Portföy / Sinyal Geçmişi     │
└─────────────────────────────────────────────────────┘
```

---

## ⚙️ Gereksinimler

- **Docker & Docker Compose** (PostgreSQL + RabbitMQ için)
- **.NET 8 SDK**
- **Python 3.10+**
- **Telegram Bot Token** (bildirim için, opsiyonel)

---

## 🚀 Kurulum

### 1. Repoyu Klonla

```bash
git clone https://github.com/KULLANICI_ADI/StockMarketAppV2.git
cd StockMarketAppV2
```

### 2. Environment Dosyasını Oluştur

```bash
cp .env.example .env
```

`.env` dosyasını düzenle:

```env
# PostgreSQL
DB_USER=postgres
DB_PASSWORD=guclu_bir_sifre_gir
DB_NAME=borsa_db
DB_HOST=localhost
DB_PORT=5433

# RabbitMQ
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guclu_bir_sifre_gir
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672

# Telegram (opsiyonel)
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=987654321
```

### 3. `appsettings.json` Oluştur

`BorsaAPI/appsettings.json` dosyasını oluştur:

```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Host=localhost;Port=5433;Database=borsa_db;Username=postgres;Password=ŞIFRE"
  },
  "RabbitMQ": {
    "Host": "localhost",
    "Port": 5672,
    "Username": "guest",
    "Password": "ŞIFRE"
  },
  "Logging": {
    "LogLevel": { "Default": "Information" }
  }
}
```

### 4. Python Bağımlılıklarını Yükle

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
# veya: source .venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

### 5. `src/config.py` Oluştur

```python
import os
from dotenv import load_dotenv
load_dotenv()

DB_AYARLARI = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 5433)),
    "dbname":   os.getenv("DB_NAME", "borsa_db"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

RABBITMQ_HOST     = os.getenv("RABBITMQ_HOST",     "localhost")
RABBITMQ_PORT     = int(os.getenv("RABBITMQ_PORT", 5672))
RABBITMQ_USER     = os.getenv("RABBITMQ_USER",     "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID",   "")

HISSELER = [
    "AKBNK", "ARCLK", "ASELS", "BIMAS", "EKGYO",
    "EREGL", "FROTO", "GARAN", "GUBRF", "HEKTS",
    "KCHOL", "KOZAL", "KRDMD", "MAVI", "MGROS",
    "OTKAR", "PGSUS", "SAHOL", "SASA", "SDTTR",
    "SISE",  "TAVHL", "TCELL", "THYAO", "TKFEN",
    "TOASO", "TTKOM", "TUPRS", "VAKBN", "YKBNK",
    # ... tüm hisseler config.py içinde tanımlı
]
```

### 6. Veritabanı ve RabbitMQ'yu Başlat

```bash
docker-compose up -d
```

PostgreSQL otomatik olarak 3 migration dosyasını çalıştırır:
- `001_create_hisseler.sql` — Ana hisseler tablosu
- `002_add_unified_columns.sql` — Unified score sütunları
- `003_signal_history.sql` — Sinyal geçmişi tablosu

### 7. C# API'yi Başlat

```bash
cd BorsaAPI
dotnet run
```

API `http://localhost:5158` adresinde çalışır.

### 8. Python Worker'ı Başlat

```bash
python src/main.py
```

---

## 📱 Telegram Bot Kurulumu

1. Telegram'da `@BotFather`'a `/newbot` komutu gönder
2. Bot token'ını al → `.env` dosyasına yaz
3. Botuna bir mesaj gönder, ardından şu URL'yi ziyaret et:
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
4. `chat.id` değerini al → `.env` dosyasına yaz

---

## 📈 Telegram Bildirim Türleri

### 1. Trend Hunter Bildirimi
BUY veya STRONG_BUY sinyali gelince:
```
🚀 STRONG_BUY — SDTTR

📊 Teknik: RSI: 42.3 | ADX: 38.1 | Score: 85
💰 Fiyat: 45.20 ₺
🎯 Hedef: 52.00 ₺  🛡️ Stop: 41.50 ₺
```

### 2. Smart Picks Bildirimi
Yüksek Unified Score'lu sinyallerde:
```
💎 DIAMOND — SDTTR

🏆 Unified Score: 100 | STRONG_BUY
🌍 Market Regime: BULL
🏷️ Tags: Strong Trend, Smart Money In, Long-Term Bull
```

### Akıllı Cooldown Sistemi
| Sinyal | Cooldown |
|---|---|
| Sinyal yükseldi (BUY→STRONG_BUY) | Her zaman gönder |
| Skor +8 puan atladı | Min 1 saat sonra |
| STRONG_BUY devam ediyor | 4 saat sonra |
| BUY devam ediyor | 6 saat sonra |
| WATCH devam ediyor | 8 saat sonra |

---

## 📊 Excel Raporu

Her analiz döngüsünün sonunda `data/sinyal_gecmisi.xlsx` otomatik güncellenir.

Manuel çalıştırmak için:
```bash
python src/excel_exporter.py
```

**Excel içeriği:**
- Sembol, Tarih, Sinyal (renk kodlu satırlar)
- Conviction seviyesi (💎/🥇/🥈/🥉)
- Giriş / Stop / Hedef fiyat + Risk/Ödül oranı
- RSI, ADX, MACD
- Market Regime, Strateji, Tags
- T+1 / T+5 / T+21 fiyat ve % performans (ilerleyen günlerde dolar)
- Özet sayfası: toplam sinyal, ortalama performanslar

---

## 🗂️ Proje Yapısı

```
StockMarketAppV2/
├── BorsaAPI/               # C# .NET 8 Backend
│   ├── Controller/         # API endpoints
│   ├── Models/             # Hisse, SignalHistory modelleri
│   ├── Services/           # HisseRepository, HisseService
│   ├── Hubs/               # SignalR BorsaHub
│   ├── Infrastructure/     # RabbitMQ Consumer
│   └── wwwroot/            # Frontend (HTML/JS/CSS)
├── src/                    # Python Worker
│   ├── main.py             # Ana döngü ve orkestrasyon
│   ├── config.py           # Konfigürasyon (gitignore'da)
│   ├── excel_exporter.py   # Excel rapor üretici
│   └── core/
│       ├── analiz.py           # Veri çekme (TvDatafeed/YFinance)
│       ├── trend_engine.py     # Trend Hunter sinyal motoru
│       ├── pro_engine.py       # Pro/Institutional analiz motoru
│       ├── telegram_notifier.py # Telegram bildirim gönderici
│       ├── notification_guard.py # Akıllı cooldown/dedup sistemi
│       └── rabbitmq_manager.py  # RabbitMQ bağlantı yöneticisi
├── migrations/             # PostgreSQL migration SQL dosyaları
├── data/                   # Üretilen veriler (gitignore'da)
│   └── sinyal_gecmisi.xlsx
├── docker-compose.yml      # PostgreSQL + RabbitMQ
├── requirements.txt        # Python bağımlılıkları
└── .env.example            # Örnek environment değişkenleri
```

---

## 🔌 API Endpoint'leri

| Method | URL | Açıklama |
|---|---|---|
| GET | `/api/hisseler` | Tüm hisse verilerini döner |
| GET | `/api/hisseler?onlyTrend=true` | Sadece BUY/STRONG_BUY sinyallerini döner |
| GET | `/api/market/pro` | Smart Picks / Pro Engine verisi |
| GET | `/api/signals/history` | Sinyal geçmişi (JWT parametreleri: sembol, limit) |
| WS  | `/borsahub` | SignalR gerçek zamanlı güncellemeler |

---

## 🛠️ Teknoloji Yığını

| Katman | Teknoloji |
|---|---|
| **Backend** | C# .NET 8, ASP.NET Core, SignalR |
| **İş Mantığı** | Python 3.10, Pandas, Pandas-TA |
| **Veri Kaynağı** | TvDatafeed (TradingView), Yahoo Finance |
| **Mesajlaşma** | RabbitMQ (AMQP) |
| **Veritabanı** | PostgreSQL 15 |
| **Frontend** | HTML5, Vanilla JS, Tailwind CSS |
| **Bildirim** | Telegram Bot API |
| **Raporlama** | OpenPyXL (Excel) |
| **Konteyner** | Docker, Docker Compose |

---

## ⚠️ Önemli Notlar

- **Yatırım tavsiyesi değildir.** Bu sistem eğitim ve araştırma amaçlıdır.
- TvDatafeed ücretsiz olup veri kalitesi değişkenlik gösterebilir.
- Bot Borsa İstanbul saatleri dışında da çalışır; bu durumlarda sinyal kalitesi düşük olabilir.
- `data/` klasörü git tarafından izlenmez; Excel dosyası ve bildirim state'i burada tutulur.

---

## 📄 Lisans

Bu proje kişisel kullanım amaçlıdır.
