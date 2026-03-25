
using BorsaAPI.Models;
using Npgsql;
using System.Text;

namespace BorsaAPI.Services
{
    public class StockRepository : IStockRepository
    {
        private readonly string _connectionString;

        public StockRepository(IConfiguration configuration)
        {
            _connectionString = configuration.GetConnectionString("BorsaDb") ?? string.Empty;
        }

        public List<Stock> GetAll(StockFilterDto filter)
        {
            var stockList = new List<Stock>();

            using (var conn = new NpgsqlConnection(_connectionString))
            {
                conn.Open();
                var sqlBuilder = new StringBuilder("SELECT * FROM stocks WHERE 1=1");
                var cmd = new NpgsqlCommand();
                cmd.Connection = conn;

                if (filter.MinScore.HasValue)
                {
                    sqlBuilder.Append(" AND score >= @minScore");
                    cmd.Parameters.AddWithValue("@minScore", filter.MinScore.Value);
                }
                if (!string.IsNullOrEmpty(filter.Signal) && filter.Signal != "All")
                {
                    sqlBuilder.Append(" AND signal = @signal");
                    cmd.Parameters.AddWithValue("@signal", filter.Signal);
                }
                if (!string.IsNullOrEmpty(filter.Strategy) && filter.Strategy != "All")
                {
                    sqlBuilder.Append(" AND strategy = @strategy");
                    cmd.Parameters.AddWithValue("@strategy", filter.Strategy);
                }
                if (filter.MinPeRatio.HasValue)
                {
                    sqlBuilder.Append(" AND pe_ratio >= @minPeRatio");
                    cmd.Parameters.AddWithValue("@minPeRatio", filter.MinPeRatio.Value);
                }
                if (filter.MaxPeRatio.HasValue)
                {
                    sqlBuilder.Append(" AND pe_ratio <= @maxPeRatio");
                    cmd.Parameters.AddWithValue("@maxPeRatio", filter.MaxPeRatio.Value);
                }
                if (filter.MinPbRatio.HasValue)
                {
                    sqlBuilder.Append(" AND pb_ratio >= @minPbRatio");
                    cmd.Parameters.AddWithValue("@minPbRatio", filter.MinPbRatio.Value);
                }
                if (filter.MaxPbRatio.HasValue)
                {
                    sqlBuilder.Append(" AND pb_ratio <= @maxPbRatio");
                    cmd.Parameters.AddWithValue("@maxPbRatio", filter.MaxPbRatio.Value);
                }
                if (filter.MinRsi.HasValue)
                {
                    sqlBuilder.Append(" AND rsi >= @minRsi");
                    cmd.Parameters.AddWithValue("@minRsi", filter.MinRsi.Value);
                }
                if (filter.MaxRsi.HasValue)
                {
                    sqlBuilder.Append(" AND rsi <= @maxRsi");
                    cmd.Parameters.AddWithValue("@maxRsi", filter.MaxRsi.Value);
                }
                if (filter.MinMacdHist.HasValue)
                {
                    sqlBuilder.Append(" AND macd_hist >= @minMacdHist");
                    cmd.Parameters.AddWithValue("@minMacdHist", filter.MinMacdHist.Value);
                }
                if (filter.MaxMacdHist.HasValue)
                {
                    sqlBuilder.Append(" AND macd_hist <= @maxMacdHist");
                    cmd.Parameters.AddWithValue("@maxMacdHist", filter.MaxMacdHist.Value);
                }
                if (filter.MinMacdLine.HasValue)
                {
                    sqlBuilder.Append(" AND macd_line >= @minMacdLine");
                    cmd.Parameters.AddWithValue("@minMacdLine", filter.MinMacdLine.Value);
                }
                if (filter.MaxMacdLine.HasValue)
                {
                    sqlBuilder.Append(" AND macd_line <= @maxMacdLine");
                    cmd.Parameters.AddWithValue("@maxMacdLine", filter.MaxMacdLine.Value);
                }
                if (filter.MinMacdSignal.HasValue)
                {
                    sqlBuilder.Append(" AND macd_signal >= @minMacdSignal");
                    cmd.Parameters.AddWithValue("@minMacdSignal", filter.MinMacdSignal.Value);
                }
                if (filter.MaxMacdSignal.HasValue)
                {
                    sqlBuilder.Append(" AND macd_signal <= @maxMacdSignal");
                    cmd.Parameters.AddWithValue("@maxMacdSignal", filter.MaxMacdSignal.Value);
                }
                if (filter.MinAdx.HasValue)
                {
                    sqlBuilder.Append(" AND adx >= @minAdx");
                    cmd.Parameters.AddWithValue("@minAdx", filter.MinAdx.Value);
                }
                if (filter.MaxAdx.HasValue)
                {
                    sqlBuilder.Append(" AND adx <= @maxAdx");
                    cmd.Parameters.AddWithValue("@maxAdx", filter.MaxAdx.Value);
                }
                if (filter.MinDmp.HasValue)
                {
                    sqlBuilder.Append(" AND dmp >= @minDmp");
                    cmd.Parameters.AddWithValue("@minDmp", filter.MinDmp.Value);
                }
                if (filter.MaxDmp.HasValue)
                {
                    sqlBuilder.Append(" AND dmp <= @maxDmp");
                    cmd.Parameters.AddWithValue("@maxDmp", filter.MaxDmp.Value);
                }
                if (filter.MinDmn.HasValue)
                {
                    sqlBuilder.Append(" AND dmn >= @minDmn");
                    cmd.Parameters.AddWithValue("@minDmn", filter.MinDmn.Value);
                }
                if (filter.MaxDmn.HasValue)
                {
                    sqlBuilder.Append(" AND dmn <= @maxDmn");
                    cmd.Parameters.AddWithValue("@maxDmn", filter.MaxDmn.Value);
                }
                if (filter.MinVolumeRatio.HasValue)
                {
                    sqlBuilder.Append(" AND volume_ratio >= @minVolumeRatio");
                    cmd.Parameters.AddWithValue("@minVolumeRatio", filter.MinVolumeRatio.Value);
                }
                if (filter.MaxVolumeRatio.HasValue)
                {
                    sqlBuilder.Append(" AND volume_ratio <= @maxVolumeRatio");
                    cmd.Parameters.AddWithValue("@maxVolumeRatio", filter.MaxVolumeRatio.Value);
                }

                sqlBuilder.Append(" ORDER BY symbol ASC");
                cmd.CommandText = sqlBuilder.ToString();

                using (var reader = cmd.ExecuteReader())
                {
                    while (reader.Read())
                    {
                        var stock = new Stock
                        {
                            Id           = reader.GetInt32(reader.GetOrdinal("id")),
                            Symbol       = reader.GetString(reader.GetOrdinal("symbol")),
                            Price        = reader.GetDecimal(reader.GetOrdinal("price")),
                            Sma50        = reader.GetDecimal(reader.GetOrdinal("sma50")),
                            Sma200       = reader.GetDecimal(reader.GetOrdinal("sma200")),
                            Rsi          = reader.IsDBNull(reader.GetOrdinal("rsi"))          ? 0 : reader.GetDecimal(reader.GetOrdinal("rsi")),
                            PeRatio      = reader.IsDBNull(reader.GetOrdinal("pe_ratio"))     ? 0 : reader.GetDecimal(reader.GetOrdinal("pe_ratio")),
                            PbRatio      = reader.IsDBNull(reader.GetOrdinal("pb_ratio"))     ? 0 : reader.GetDecimal(reader.GetOrdinal("pb_ratio")),
                            PricePrev    = reader.IsDBNull(reader.GetOrdinal("price_prev"))   ? 0 : reader.GetDecimal(reader.GetOrdinal("price_prev")),
                            RsiPrev      = reader.IsDBNull(reader.GetOrdinal("rsi_prev"))     ? 0 : reader.GetDecimal(reader.GetOrdinal("rsi_prev")),
                            AdxPrev      = reader.IsDBNull(reader.GetOrdinal("adx_prev"))     ? 0 : reader.GetDecimal(reader.GetOrdinal("adx_prev")),
                            MacdLine     = reader.IsDBNull(reader.GetOrdinal("macd_line"))    ? 0 : reader.GetDecimal(reader.GetOrdinal("macd_line")),
                            MacdSignal   = reader.IsDBNull(reader.GetOrdinal("macd_signal"))  ? 0 : reader.GetDecimal(reader.GetOrdinal("macd_signal")),
                            MacdHist     = reader.IsDBNull(reader.GetOrdinal("macd_hist"))    ? 0 : reader.GetDecimal(reader.GetOrdinal("macd_hist")),
                            Adx          = reader.IsDBNull(reader.GetOrdinal("adx"))          ? 0 : reader.GetDecimal(reader.GetOrdinal("adx")),
                            Dmp          = reader.IsDBNull(reader.GetOrdinal("dmp"))          ? 0 : reader.GetDecimal(reader.GetOrdinal("dmp")),
                            Dmn          = reader.IsDBNull(reader.GetOrdinal("dmn"))          ? 0 : reader.GetDecimal(reader.GetOrdinal("dmn")),
                            Atr          = reader.IsDBNull(reader.GetOrdinal("atr"))          ? 0 : reader.GetDecimal(reader.GetOrdinal("atr")),
                            VolumeRatio  = reader.IsDBNull(reader.GetOrdinal("volume_ratio")) ? 0 : reader.GetDecimal(reader.GetOrdinal("volume_ratio")),
                            LastUpdated  = reader.GetDateTime(reader.GetOrdinal("last_updated")),
                            Signal       = reader.IsDBNull(reader.GetOrdinal("signal"))       ? "NO_TRADE" : reader.GetString(reader.GetOrdinal("signal")),
                            Score        = reader.IsDBNull(reader.GetOrdinal("score"))        ? 0 : reader.GetInt32(reader.GetOrdinal("score")),
                            StopPrice    = reader.IsDBNull(reader.GetOrdinal("stop_price"))   ? 0 : reader.GetDecimal(reader.GetOrdinal("stop_price")),
                            TargetPrice  = reader.IsDBNull(reader.GetOrdinal("target_price")) ? 0 : reader.GetDecimal(reader.GetOrdinal("target_price")),
                            MacdHistPrev = reader.IsDBNull(reader.GetOrdinal("macd_hist_prev")) ? 0 : reader.GetDecimal(reader.GetOrdinal("macd_hist_prev")),
                            VolumePrev   = reader.IsDBNull(reader.GetOrdinal("volume_prev"))  ? 0 : reader.GetDecimal(reader.GetOrdinal("volume_prev")),
                            Strategy     = reader.IsDBNull(reader.GetOrdinal("strategy"))     ? "NONE" : reader.GetString(reader.GetOrdinal("strategy")),
                            MainStrategy = reader.IsDBNull(reader.GetOrdinal("main_strategy")) ? "NEUTRAL" : reader.GetString(reader.GetOrdinal("main_strategy")),
                            MarketRegime = reader.IsDBNull(reader.GetOrdinal("market_regime")) ? "SIDEWAYS" : reader.GetString(reader.GetOrdinal("market_regime")),
                            ConfidenceScore = reader.IsDBNull(reader.GetOrdinal("confidence_score")) ? 0 : reader.GetInt32(reader.GetOrdinal("confidence_score")),
                            UnifiedScore = reader.IsDBNull(reader.GetOrdinal("unified_score")) ? 0 : reader.GetInt32(reader.GetOrdinal("unified_score")),
                            Conviction   = reader.IsDBNull(reader.GetOrdinal("conviction"))   ? "BRONZE" : reader.GetString(reader.GetOrdinal("conviction")),
                        };

                        if (!reader.IsDBNull(reader.GetOrdinal("tags")))
                            stock.Tags = reader.GetFieldValue<string[]>(reader.GetOrdinal("tags"));

                        stockList.Add(stock);
                    }
                }
            }

            return stockList;
        }

        public void Save(Stock stock)
        {
            using (var conn = new NpgsqlConnection(_connectionString))
            {
                conn.Open();
                const string sql = @"
                    INSERT INTO stocks (
                        symbol, price, sma50, sma200, pe_ratio, pb_ratio, rsi,
                        macd_line, macd_signal, macd_hist, adx, dmp, dmn, volume_ratio,
                        signal, score, stop_price, target_price,
                        macd_hist_prev, volume_prev, price_prev, rsi_prev, adx_prev, atr,
                        last_updated, strategy,
                        tags, main_strategy, market_regime, confidence_score,
                        unified_score, conviction
                    )
                    VALUES (
                        @symbol, @price, @sma50, @sma200, @pe_ratio, @pb_ratio, @rsi,
                        @macd_line, @macd_signal, @macd_hist, @adx, @dmp, @dmn, @volume_ratio,
                        @signal, @score, @stop_price, @target_price,
                        @macd_hist_prev, @volume_prev, @price_prev, @rsi_prev, @adx_prev, @atr,
                        NOW(), @strategy,
                        @tags, @main_strategy, @market_regime, @confidence_score,
                        @unified_score, @conviction
                    )
                    ON CONFLICT (symbol)
                    DO UPDATE SET
                        price           = EXCLUDED.price,
                        sma50           = EXCLUDED.sma50,
                        sma200          = EXCLUDED.sma200,
                        pe_ratio        = EXCLUDED.pe_ratio,
                        pb_ratio        = EXCLUDED.pb_ratio,
                        rsi             = EXCLUDED.rsi,
                        macd_line       = EXCLUDED.macd_line,
                        macd_signal     = EXCLUDED.macd_signal,
                        macd_hist       = EXCLUDED.macd_hist,
                        adx             = EXCLUDED.adx,
                        dmp             = EXCLUDED.dmp,
                        dmn             = EXCLUDED.dmn,
                        volume_ratio    = EXCLUDED.volume_ratio,
                        signal          = EXCLUDED.signal,
                        score           = EXCLUDED.score,
                        stop_price      = EXCLUDED.stop_price,
                        target_price    = EXCLUDED.target_price,
                        macd_hist_prev  = EXCLUDED.macd_hist_prev,
                        volume_prev     = EXCLUDED.volume_prev,
                        price_prev      = EXCLUDED.price_prev,
                        rsi_prev        = EXCLUDED.rsi_prev,
                        adx_prev        = EXCLUDED.adx_prev,
                        atr             = EXCLUDED.atr,
                        last_updated    = EXCLUDED.last_updated,
                        strategy        = EXCLUDED.strategy,
                        tags            = EXCLUDED.tags,
                        main_strategy   = EXCLUDED.main_strategy,
                        market_regime   = EXCLUDED.market_regime,
                        confidence_score= EXCLUDED.confidence_score,
                        unified_score   = EXCLUDED.unified_score,
                        conviction      = EXCLUDED.conviction;";

                using (var cmd = new NpgsqlCommand(sql, conn))
                {
                    cmd.Parameters.AddWithValue("@symbol",           stock.Symbol);
                    cmd.Parameters.AddWithValue("@price",            stock.Price);
                    cmd.Parameters.AddWithValue("@sma50",            stock.Sma50);
                    cmd.Parameters.AddWithValue("@sma200",           stock.Sma200);
                    cmd.Parameters.AddWithValue("@pe_ratio",         stock.PeRatio);
                    cmd.Parameters.AddWithValue("@pb_ratio",         stock.PbRatio);
                    cmd.Parameters.AddWithValue("@rsi",              stock.Rsi);
                    cmd.Parameters.AddWithValue("@macd_line",        stock.MacdLine);
                    cmd.Parameters.AddWithValue("@macd_signal",      stock.MacdSignal);
                    cmd.Parameters.AddWithValue("@macd_hist",        stock.MacdHist);
                    cmd.Parameters.AddWithValue("@adx",              stock.Adx);
                    cmd.Parameters.AddWithValue("@dmp",              stock.Dmp);
                    cmd.Parameters.AddWithValue("@dmn",              stock.Dmn);
                    cmd.Parameters.AddWithValue("@volume_ratio",     stock.VolumeRatio);
                    cmd.Parameters.AddWithValue("@signal",           stock.Signal);
                    cmd.Parameters.AddWithValue("@score",            stock.Score);
                    cmd.Parameters.AddWithValue("@stop_price",       stock.StopPrice);
                    cmd.Parameters.AddWithValue("@target_price",     stock.TargetPrice);
                    cmd.Parameters.AddWithValue("@macd_hist_prev",   stock.MacdHistPrev);
                    cmd.Parameters.AddWithValue("@volume_prev",      stock.VolumePrev);
                    cmd.Parameters.AddWithValue("@price_prev",       stock.PricePrev);
                    cmd.Parameters.AddWithValue("@rsi_prev",         stock.RsiPrev);
                    cmd.Parameters.AddWithValue("@adx_prev",         stock.AdxPrev);
                    cmd.Parameters.AddWithValue("@atr",              stock.Atr);
                    cmd.Parameters.AddWithValue("@strategy",         stock.Strategy);
                    cmd.Parameters.AddWithValue("@tags",             (object?)stock.Tags ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@main_strategy",    stock.MainStrategy);
                    cmd.Parameters.AddWithValue("@market_regime",    stock.MarketRegime);
                    cmd.Parameters.AddWithValue("@confidence_score", stock.ConfidenceScore);
                    cmd.Parameters.AddWithValue("@unified_score",    stock.UnifiedScore);
                    cmd.Parameters.AddWithValue("@conviction",       stock.Conviction);
                    cmd.ExecuteNonQuery();
                }
            }
        }

        public void SaveSignalHistory(Stock stock)
        {
            using (var conn = new NpgsqlConnection(_connectionString))
            {
                conn.Open();

                // Duplicate guard: skip if same symbol + signal already recorded today
                const string checkSql = @"
                    SELECT COUNT(*) FROM signal_history
                    WHERE symbol     = @symbol
                      AND signal     = @signal
                      AND signal_date::date = CURRENT_DATE";

                using (var checkCmd = new NpgsqlCommand(checkSql, conn))
                {
                    checkCmd.Parameters.AddWithValue("@symbol", stock.Symbol);
                    checkCmd.Parameters.AddWithValue("@signal", stock.Signal);
                    long count = (long)(checkCmd.ExecuteScalar() ?? 0L);
                    if (count > 0) return;
                }

                const string sql = @"
                    INSERT INTO signal_history (
                        symbol, signal_date, signal, unified_score, conviction, score,
                        price, stop_price, target_price,
                        rsi, adx, macd_hist,
                        market_regime, main_strategy, tags
                    ) VALUES (
                        @symbol, NOW(), @signal, @unified_score, @conviction, @score,
                        @price, @stop_price, @target_price,
                        @rsi, @adx, @macd_hist,
                        @market_regime, @main_strategy, @tags
                    )";

                using (var cmd = new NpgsqlCommand(sql, conn))
                {
                    cmd.Parameters.AddWithValue("@symbol",        stock.Symbol);
                    cmd.Parameters.AddWithValue("@signal",        stock.Signal);
                    cmd.Parameters.AddWithValue("@unified_score", stock.UnifiedScore);
                    cmd.Parameters.AddWithValue("@conviction",    stock.Conviction);
                    cmd.Parameters.AddWithValue("@score",         stock.Score);
                    cmd.Parameters.AddWithValue("@price",         stock.Price);
                    cmd.Parameters.AddWithValue("@stop_price",    stock.StopPrice);
                    cmd.Parameters.AddWithValue("@target_price",  stock.TargetPrice);
                    cmd.Parameters.AddWithValue("@rsi",           stock.Rsi);
                    cmd.Parameters.AddWithValue("@adx",           stock.Adx);
                    cmd.Parameters.AddWithValue("@macd_hist",     stock.MacdHist);
                    cmd.Parameters.AddWithValue("@market_regime", stock.MarketRegime);
                    cmd.Parameters.AddWithValue("@main_strategy", stock.MainStrategy);
                    cmd.Parameters.AddWithValue("@tags",          (object?)stock.Tags ?? DBNull.Value);
                    cmd.ExecuteNonQuery();
                }
            }
        }

        public List<SignalHistory> GetSignalHistory(string? symbol, int limit)
        {
            var list = new List<SignalHistory>();
            using (var conn = new NpgsqlConnection(_connectionString))
            {
                conn.Open();
                string sql = string.IsNullOrEmpty(symbol)
                    ? "SELECT * FROM signal_history ORDER BY signal_date DESC LIMIT @limit"
                    : "SELECT * FROM signal_history WHERE symbol = @symbol ORDER BY signal_date DESC LIMIT @limit";

                using (var cmd = new NpgsqlCommand(sql, conn))
                {
                    cmd.Parameters.AddWithValue("@limit", limit);
                    if (!string.IsNullOrEmpty(symbol))
                        cmd.Parameters.AddWithValue("@symbol", symbol);

                    using (var reader = cmd.ExecuteReader())
                    {
                        while (reader.Read())
                        {
                            var sh = new SignalHistory
                            {
                                Id           = reader.GetInt32(reader.GetOrdinal("id")),
                                Symbol       = reader.GetString(reader.GetOrdinal("symbol")),
                                SignalDate   = reader.GetDateTime(reader.GetOrdinal("signal_date")),
                                Signal       = reader.IsDBNull(reader.GetOrdinal("signal"))        ? "NO_TRADE" : reader.GetString(reader.GetOrdinal("signal")),
                                UnifiedScore = reader.IsDBNull(reader.GetOrdinal("unified_score")) ? 0 : reader.GetInt32(reader.GetOrdinal("unified_score")),
                                Conviction   = reader.IsDBNull(reader.GetOrdinal("conviction"))    ? "BRONZE" : reader.GetString(reader.GetOrdinal("conviction")),
                                Score        = reader.IsDBNull(reader.GetOrdinal("score"))         ? 0 : reader.GetInt32(reader.GetOrdinal("score")),
                                Price        = reader.IsDBNull(reader.GetOrdinal("price"))         ? 0 : reader.GetDecimal(reader.GetOrdinal("price")),
                                StopPrice    = reader.IsDBNull(reader.GetOrdinal("stop_price"))    ? 0 : reader.GetDecimal(reader.GetOrdinal("stop_price")),
                                TargetPrice  = reader.IsDBNull(reader.GetOrdinal("target_price"))  ? 0 : reader.GetDecimal(reader.GetOrdinal("target_price")),
                                Rsi          = reader.IsDBNull(reader.GetOrdinal("rsi"))           ? 0 : reader.GetDecimal(reader.GetOrdinal("rsi")),
                                Adx          = reader.IsDBNull(reader.GetOrdinal("adx"))           ? 0 : reader.GetDecimal(reader.GetOrdinal("adx")),
                                MacdHist     = reader.IsDBNull(reader.GetOrdinal("macd_hist"))     ? 0 : reader.GetDecimal(reader.GetOrdinal("macd_hist")),
                                MarketRegime = reader.IsDBNull(reader.GetOrdinal("market_regime")) ? "SIDEWAYS" : reader.GetString(reader.GetOrdinal("market_regime")),
                                MainStrategy = reader.IsDBNull(reader.GetOrdinal("main_strategy")) ? "NEUTRAL" : reader.GetString(reader.GetOrdinal("main_strategy")),
                                Tags         = reader.IsDBNull(reader.GetOrdinal("tags"))          ? Array.Empty<string>() : reader.GetFieldValue<string[]>(reader.GetOrdinal("tags")),
                                Price1Day    = reader.IsDBNull(reader.GetOrdinal("price_1day"))    ? null : reader.GetDecimal(reader.GetOrdinal("price_1day")),
                                Price1Week   = reader.IsDBNull(reader.GetOrdinal("price_1week"))   ? null : reader.GetDecimal(reader.GetOrdinal("price_1week")),
                                Price1Month  = reader.IsDBNull(reader.GetOrdinal("price_1month"))  ? null : reader.GetDecimal(reader.GetOrdinal("price_1month")),
                                Perf1Day     = reader.IsDBNull(reader.GetOrdinal("perf_1day"))     ? null : reader.GetDecimal(reader.GetOrdinal("perf_1day")),
                                Perf1Week    = reader.IsDBNull(reader.GetOrdinal("perf_1week"))    ? null : reader.GetDecimal(reader.GetOrdinal("perf_1week")),
                                Perf1Month   = reader.IsDBNull(reader.GetOrdinal("perf_1month"))   ? null : reader.GetDecimal(reader.GetOrdinal("perf_1month")),
                            };
                            list.Add(sh);
                        }
                    }
                }
            }
            return list;
        }
    }
}
