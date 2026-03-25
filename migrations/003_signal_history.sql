-- Migration 003: Signal History Table
-- Records every BUY/STRONG_BUY/WATCH signal as a separate row
-- and tracks how the stock moved after the signal (1d/1w/1m)

CREATE TABLE IF NOT EXISTS signal_history (
    id              SERIAL PRIMARY KEY,
    symbol          VARCHAR(20) NOT NULL,
    signal_date     TIMESTAMP DEFAULT NOW(),

    -- Signal Info
    signal          VARCHAR(50),
    unified_score   INTEGER DEFAULT 0,
    conviction      VARCHAR(20),
    score           INTEGER DEFAULT 0,

    -- Price at Signal Time
    price           DECIMAL DEFAULT 0,
    stop_price      DECIMAL DEFAULT 0,
    target_price    DECIMAL DEFAULT 0,

    -- Indicators at Signal Time (Trend Hunter)
    rsi             DECIMAL DEFAULT 0,
    adx             DECIMAL DEFAULT 0,
    macd_hist       DECIMAL DEFAULT 0,

    -- Market Context
    market_regime   VARCHAR(20) DEFAULT 'SIDEWAYS',
    main_strategy   VARCHAR(50) DEFAULT 'NEUTRAL',
    tags            TEXT[],

    -- Future Price Tracking (filled automatically by Python worker)
    price_1day      DECIMAL,    -- closing price at T+1
    price_1week     DECIMAL,    -- closing price at T+5
    price_1month    DECIMAL,    -- closing price at T+21

    -- Performance % (calculated when filled)
    perf_1day       DECIMAL,
    perf_1week      DECIMAL,
    perf_1month     DECIMAL
);

CREATE INDEX IF NOT EXISTS idx_signal_history_symbol ON signal_history(symbol);
CREATE INDEX IF NOT EXISTS idx_signal_history_date   ON signal_history(signal_date);
CREATE INDEX IF NOT EXISTS idx_signal_history_signal ON signal_history(signal);
