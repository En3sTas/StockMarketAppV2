-- Migration: Full Schema for Hisseler Table
-- Contains all columns used by HisseRepository and Pro Engine
-- Usage: Run via apply_migration.py or directly against PostgreSQL

CREATE TABLE IF NOT EXISTS "hisseler" (
    "id"                  SERIAL PRIMARY KEY,
    "sembol"              VARCHAR(20) NOT NULL UNIQUE,

    -- Core Price & Indicators
    "fiyat"               DECIMAL DEFAULT 0,
    "sma_50"              DECIMAL DEFAULT 0,
    "sma_200"             DECIMAL DEFAULT 0,
    "fk"                  DECIMAL DEFAULT 0,
    "pd_dd"               DECIMAL DEFAULT 0,
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
    "hacim_orani"         DECIMAL DEFAULT 0,

    -- Trade Signals (Legacy Engine)
    "signal"              VARCHAR(50) DEFAULT 'NO_TRADE',
    "score"               INTEGER DEFAULT 0,
    "stop_price"          DECIMAL DEFAULT 0,
    "target_price"        DECIMAL DEFAULT 0,

    -- Previous Day Values
    "macd_hist_onceki"    DECIMAL DEFAULT 0,
    "hacim_onceki"        DECIMAL DEFAULT 0,
    "fiyat_onceki"        DECIMAL DEFAULT 0,
    "rsi_onceki"          DECIMAL DEFAULT 0,
    "adx_onceki"          DECIMAL DEFAULT 0,

    -- ATR
    "atr"                 DECIMAL DEFAULT 0,

    -- Metadata
    "son_guncelleme"      TIMESTAMP DEFAULT NOW(),
    "strategy"            VARCHAR(20) DEFAULT 'NONE',

    -- Pro Engine (Institutional Grade)
    "tags"                TEXT[],
    "main_strategy"       VARCHAR(50) DEFAULT 'NEUTRAL',
    "market_regime"       VARCHAR(20) DEFAULT 'SIDEWAYS',
    "confidence_score"    INTEGER DEFAULT 0
);

-- Ensure Pro Engine columns exist for existing databases (idempotent)
ALTER TABLE "hisseler" ADD COLUMN IF NOT EXISTS "tags"              TEXT[];
ALTER TABLE "hisseler" ADD COLUMN IF NOT EXISTS "main_strategy"     VARCHAR(50) DEFAULT 'NEUTRAL';
ALTER TABLE "hisseler" ADD COLUMN IF NOT EXISTS "market_regime"     VARCHAR(20) DEFAULT 'SIDEWAYS';
ALTER TABLE "hisseler" ADD COLUMN IF NOT EXISTS "confidence_score"  INTEGER DEFAULT 0;
