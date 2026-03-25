-- Migration 001: Create stocks table (full schema — English column names)
-- Usage: Run via apply_migration.py or directly against PostgreSQL

CREATE TABLE IF NOT EXISTS "stocks" (
    "id"                  SERIAL PRIMARY KEY,
    "symbol"              VARCHAR(20) NOT NULL UNIQUE,

    -- Core Price & Indicators
    "price"               DECIMAL DEFAULT 0,
    "sma50"               DECIMAL DEFAULT 0,
    "sma200"              DECIMAL DEFAULT 0,
    "pe_ratio"            DECIMAL DEFAULT 0,
    "pb_ratio"            DECIMAL DEFAULT 0,
    "rsi"                 DECIMAL DEFAULT 0,

    -- MACD
    "macd_line"           DECIMAL DEFAULT 0,
    "macd_signal"         DECIMAL DEFAULT 0,
    "macd_hist"           DECIMAL DEFAULT 0,

    -- ADX & Directional Movement
    "adx"                 DECIMAL DEFAULT 0,
    "dmp"                 DECIMAL DEFAULT 0,
    "dmn"                 DECIMAL DEFAULT 0,

    -- Volume
    "volume_ratio"        DECIMAL DEFAULT 0,

    -- Trade Signals
    "signal"              VARCHAR(50) DEFAULT 'NO_TRADE',
    "score"               INTEGER DEFAULT 0,
    "stop_price"          DECIMAL DEFAULT 0,
    "target_price"        DECIMAL DEFAULT 0,

    -- Previous Values
    "macd_hist_prev"      DECIMAL DEFAULT 0,
    "volume_prev"         DECIMAL DEFAULT 0,
    "price_prev"          DECIMAL DEFAULT 0,
    "rsi_prev"            DECIMAL DEFAULT 0,
    "adx_prev"            DECIMAL DEFAULT 0,

    -- ATR
    "atr"                 DECIMAL DEFAULT 0,

    -- Metadata
    "last_updated"        TIMESTAMP DEFAULT NOW(),
    "strategy"            VARCHAR(20) DEFAULT 'NONE',

    -- Pro Engine (Institutional Grade)
    "tags"                TEXT[],
    "main_strategy"       VARCHAR(50) DEFAULT 'NEUTRAL',
    "market_regime"       VARCHAR(20) DEFAULT 'SIDEWAYS',
    "confidence_score"    INTEGER DEFAULT 0,

    -- Unified Conviction Engine
    "unified_score"       INTEGER DEFAULT 0,
    "conviction"          VARCHAR(20) DEFAULT 'BRONZE'
);

-- Idempotent additions for existing databases
ALTER TABLE "stocks" ADD COLUMN IF NOT EXISTS "tags"              TEXT[];
ALTER TABLE "stocks" ADD COLUMN IF NOT EXISTS "main_strategy"     VARCHAR(50) DEFAULT 'NEUTRAL';
ALTER TABLE "stocks" ADD COLUMN IF NOT EXISTS "market_regime"     VARCHAR(20) DEFAULT 'SIDEWAYS';
ALTER TABLE "stocks" ADD COLUMN IF NOT EXISTS "confidence_score"  INTEGER DEFAULT 0;
ALTER TABLE "stocks" ADD COLUMN IF NOT EXISTS "unified_score"     INTEGER DEFAULT 0;
ALTER TABLE "stocks" ADD COLUMN IF NOT EXISTS "conviction"        VARCHAR(20) DEFAULT 'BRONZE';
