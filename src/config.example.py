# Database Configuration for PostgreSQL
DB_AYARLARI = {
    "host": "localhost",
    "port": 5432,
    "database": "borsa_db",  # Change to your database name
    "user": "postgres",      # Change to your PostgreSQL username
    "password": "CHANGE_THIS_PASSWORD"  # Change to your PostgreSQL password
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
