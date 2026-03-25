
import os
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Database Connection Settings (reads from .env)
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5433")),
    "database": os.getenv("DB_NAME", "borsa_db"),       # Change to your database name
    "user": os.getenv("DB_USER", "postgres"),            # Change to your PostgreSQL username
    "password": os.getenv("DB_PASSWORD", "CHANGE_THIS_PASSWORD")  # Change to your PostgreSQL password
}

# RabbitMQ Connection Settings (reads from .env)
RABBITMQ_CONFIG = {
    "host": os.getenv("RABBITMQ_HOST", "localhost"),
    "port": int(os.getenv("RABBITMQ_PORT", "5672")),
    "user": os.getenv("RABBITMQ_USER", "guest"),
    "password": os.getenv("RABBITMQ_PASSWORD", "CHANGE_THIS_PASSWORD")
}

# Turkish Stock Symbols to Monitor (BIST - Borsa Istanbul)
# Add or remove symbols as needed
HISSELER = [
    "AEFES", "AGHOL", "AHGAZ", "AKBNK", "AKCNS", "AKFGY", "AKSA", "ALARK", "ALBRK",
    "ALFAS", "ANSGR", "ARCLK", "ASELS", "ASTOR", "AYDEM", "BAGFS", "BASGZ", "BERA", "BIMAS",
    "BIOEN", "BRSAN", "BRYAT", "BUCIM", "CANTE", "CCOLA", "CEMTS", "CIMSA", "CWENE", "DOHOL",
    "DOAS", "ECILC", "ECZYT", "EGEEN", "EKGYO", "ENJSA", "ENKAI", "EREGL", "EUPWR", "EUREN",
    "FENER", "FROTO", "GARAN", "GENIL", "GESAN", "GLYHO", "GSDHO", "GUBRF", "GWIND", "HALKB",
    "HEKTS", "IPEKE", "ISCTR", "ISDMR", "ISGYO", "ISMEN", "IZENR", "KCAER", "KCHOL", "KLSER",
    "KMPUR", "KONTR", "KONYA", "KORDS","KOZAL", "KRDMD", "KZBGY", "MAVI", "MGROS",
    "MIATK", "ODAS", "OTKAR", "OYAKC", "PETKM", "PGSUS", "PSGYO", "QUAGR", "SAHOL", "SASA",
    "SAYAS", "SDTTR", "SISE", "SKBNK", "SMRTG", "SOKM", "TABGD", "TAVHL", "TCELL", "THYAO",
    "TKFEN", "TOASO", "TSKB", "TTKOM", "TTRAK", "TUKAS", "TUPRS", "TURSG", "ULKER", "VAKBN",
    "VESTL", "YEOTK", "YKBNK", "ZOREN"
]
