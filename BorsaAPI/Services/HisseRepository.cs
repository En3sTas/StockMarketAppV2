
using BorsaAPI.Models;
using Npgsql;
using System.Text;

namespace BorsaAPI.Services
{
    public class HisseRepository : IHisseRepository
    {
        private readonly string _connectionString;

        public HisseRepository(IConfiguration configuration)
        {
            _connectionString = configuration.GetConnectionString("BorsaDb") ?? string.Empty;
        }

        public List<Hisse> TumHisseleriGetir(HisselerFilterDto filter)
        {
            List<Hisse> hisseListesi = new List<Hisse>();

            using (NpgsqlConnection conn = new NpgsqlConnection(_connectionString))
            {
                conn.Open();
                StringBuilder sqlBuilder = new StringBuilder("SELECT * FROM Hisseler WHERE 1=1");
                NpgsqlCommand cmd = new NpgsqlCommand();
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
                
                if (filter.MinFk.HasValue)
                {
                    sqlBuilder.Append(" AND fk >= @minFk");
                    cmd.Parameters.AddWithValue("@minFk", filter.MinFk.Value);
                }
                if (filter.MaxFk.HasValue)
                {
                    sqlBuilder.Append(" AND fk <= @maxFk");
                    cmd.Parameters.AddWithValue("@maxFk", filter.MaxFk.Value);
                }
                if (filter.MinPdDd.HasValue)
                {
                    sqlBuilder.Append(" AND pd_dd >= @minPdDd");
                    cmd.Parameters.AddWithValue("@minPdDd", filter.MinPdDd.Value);
                }
                if (filter.MaxPdDd.HasValue)
                {
                    sqlBuilder.Append(" AND pd_dd <= @maxPdDd");
                    cmd.Parameters.AddWithValue("@maxPdDd", filter.MaxPdDd.Value);
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
                if (filter.MinHacimOrani.HasValue)
                {
                    sqlBuilder.Append(" AND hacim_orani >= @minHacimOrani");
                    cmd.Parameters.AddWithValue("@minHacimOrani", filter.MinHacimOrani.Value);
                }
                if (filter.MaxHacimOrani.HasValue)
                {
                    sqlBuilder.Append(" AND hacim_orani <= @maxHacimOrani");
                    cmd.Parameters.AddWithValue("@maxHacimOrani", filter.MaxHacimOrani.Value);
                }
                sqlBuilder.Append(" ORDER BY sembol ASC");
                cmd.CommandText = sqlBuilder.ToString();

                using (NpgsqlDataReader reader = cmd.ExecuteReader())
                {
                    while (reader.Read())
                    {
                        Hisse hisse = new Hisse();
                        hisse.Id = reader.GetInt32(reader.GetOrdinal("id"));
                        hisse.Sembol = reader.GetString(reader.GetOrdinal("sembol"));
                        hisse.Fiyat = reader.GetDecimal(reader.GetOrdinal("fiyat"));
                        hisse.Sma50 = reader.GetDecimal(reader.GetOrdinal("sma_50"));
                        hisse.Sma200 = reader.GetDecimal(reader.GetOrdinal("sma_200"));
                        hisse.Rsi = reader.IsDBNull(reader.GetOrdinal("rsi")) ? 0 : reader.GetDecimal(reader.GetOrdinal("rsi"));
                        hisse.Fk = reader.IsDBNull(reader.GetOrdinal("fk")) ? 0 : reader.GetDecimal(reader.GetOrdinal("fk"));
                        hisse.PdDd = reader.IsDBNull(reader.GetOrdinal("pd_dd")) ? 0 : reader.GetDecimal(reader.GetOrdinal("pd_dd"));
                        
                        hisse.FiyatOnceki = reader.IsDBNull(reader.GetOrdinal("fiyat_onceki")) ? 0 : reader.GetDecimal(reader.GetOrdinal("fiyat_onceki"));
                        hisse.RsiOnceki = reader.IsDBNull(reader.GetOrdinal("rsi_onceki")) ? 0 : reader.GetDecimal(reader.GetOrdinal("rsi_onceki"));
                        hisse.AdxOnceki = reader.IsDBNull(reader.GetOrdinal("adx_onceki")) ? 0 : reader.GetDecimal(reader.GetOrdinal("adx_onceki"));
                        
                        hisse.MacdLine = reader.IsDBNull(reader.GetOrdinal("macd_line")) ? 0 : reader.GetDecimal(reader.GetOrdinal("macd_line"));
                        hisse.MacdSignal = reader.IsDBNull(reader.GetOrdinal("macd_signal")) ? 0 : reader.GetDecimal(reader.GetOrdinal("macd_signal"));
                        hisse.MacdHist = reader.IsDBNull(reader.GetOrdinal("macd_hist")) ? 0 : reader.GetDecimal(reader.GetOrdinal("macd_hist"));
                        
                        hisse.Adx = reader.IsDBNull(reader.GetOrdinal("adx")) ? 0 : reader.GetDecimal(reader.GetOrdinal("adx"));
                        hisse.Dmp = reader.IsDBNull(reader.GetOrdinal("dmp")) ? 0 : reader.GetDecimal(reader.GetOrdinal("dmp"));
                        hisse.Dmn = reader.IsDBNull(reader.GetOrdinal("dmn")) ? 0 : reader.GetDecimal(reader.GetOrdinal("dmn"));
                        hisse.Atr = reader.IsDBNull(reader.GetOrdinal("atr")) ? 0 : reader.GetDecimal(reader.GetOrdinal("atr"));

                        hisse.HacimOrani = reader.IsDBNull(reader.GetOrdinal("hacim_orani")) ? 0 : reader.GetDecimal(reader.GetOrdinal("hacim_orani"));
                        hisse.SonGuncelleme = reader.GetDateTime(reader.GetOrdinal("son_guncelleme"));

                        // Expanded Fields
                        hisse.Signal = reader.IsDBNull(reader.GetOrdinal("signal")) ? "NO_TRADE" : reader.GetString(reader.GetOrdinal("signal"));
                        hisse.Score = reader.IsDBNull(reader.GetOrdinal("score")) ? 0 : reader.GetInt32(reader.GetOrdinal("score"));
                        hisse.StopPrice = reader.IsDBNull(reader.GetOrdinal("stop_price")) ? 0 : reader.GetDecimal(reader.GetOrdinal("stop_price"));
                        hisse.TargetPrice = reader.IsDBNull(reader.GetOrdinal("target_price")) ? 0 : reader.GetDecimal(reader.GetOrdinal("target_price"));
                        hisse.MacdHistOnceki = reader.IsDBNull(reader.GetOrdinal("macd_hist_onceki")) ? 0 : reader.GetDecimal(reader.GetOrdinal("macd_hist_onceki"));
                        hisse.HacimOnceki = reader.IsDBNull(reader.GetOrdinal("hacim_onceki")) ? 0 : reader.GetDecimal(reader.GetOrdinal("hacim_onceki"));
                        hisse.Strategy = reader.IsDBNull(reader.GetOrdinal("strategy")) ? "NONE" : reader.GetString(reader.GetOrdinal("strategy"));

                        // Pro Engine Fields
                        hisse.MainStrategy = reader.IsDBNull(reader.GetOrdinal("main_strategy")) ? "NEUTRAL" : reader.GetString(reader.GetOrdinal("main_strategy"));
                        hisse.MarketRegime = reader.IsDBNull(reader.GetOrdinal("market_regime")) ? "SIDEWAYS" : reader.GetString(reader.GetOrdinal("market_regime"));
                        hisse.ConfidenceScore = reader.IsDBNull(reader.GetOrdinal("confidence_score")) ? 0 : reader.GetInt32(reader.GetOrdinal("confidence_score"));
                        
                        if (!reader.IsDBNull(reader.GetOrdinal("tags")))
                        {
                            hisse.Tags = reader.GetFieldValue<string[]>(reader.GetOrdinal("tags"));
                        }

                        // Unified Conviction Engine Fields
                        hisse.UnifiedScore = reader.IsDBNull(reader.GetOrdinal("unified_score")) ? 0 : reader.GetInt32(reader.GetOrdinal("unified_score"));
                        hisse.Conviction = reader.IsDBNull(reader.GetOrdinal("conviction")) ? "BRONZE" : reader.GetString(reader.GetOrdinal("conviction"));

                        hisseListesi.Add(hisse);
                    }
                }
            }

            return hisseListesi;
        }

        public void Kaydet(Hisse hisse)
        {
            using (NpgsqlConnection conn = new NpgsqlConnection(_connectionString))
            {
                conn.Open();
                string sql = @"
                    INSERT INTO Hisseler (
                        sembol, fiyat, sma_50, sma_200, fk, pd_dd, rsi, macd_line, macd_signal, macd_hist, adx, dmp, dmn, hacim_orani, 
                        signal, score, stop_price, target_price, macd_hist_onceki, hacim_onceki,
                        fiyat_onceki, rsi_onceki, adx_onceki, atr,
                        son_guncelleme, strategy,
                        tags, main_strategy, market_regime, confidence_score,
                        unified_score, conviction
                    )
                    VALUES (@sembol, @fiyat, @sma50, @sma200, @fk, @pd_dd, @rsi, @macd_line, @macd_signal, @macd_hist, @adx, @dmp, @dmn, @hacim_orani, 
                        @signal, @score, @stop_price, @target_price, @macd_hist_onceki, @hacim_onceki,
                        @fiyat_onceki, @rsi_onceki, @adx_onceki, @atr, NOW(), @strategy,
                        @tags, @main_strategy, @market_regime, @confidence_score,
                        @unified_score, @conviction)
                    ON CONFLICT (sembol) 
                    DO UPDATE SET 
                        fiyat = EXCLUDED.fiyat,
                        sma_50 = EXCLUDED.sma_50,
                        sma_200 = EXCLUDED.sma_200,
                        fk = EXCLUDED.fk,
                        pd_dd = EXCLUDED.pd_dd,
                        rsi = EXCLUDED.rsi,
                        macd_line = EXCLUDED.macd_line,
                        macd_signal = EXCLUDED.macd_signal,
                        macd_hist= EXCLUDED.macd_hist,
                        adx = EXCLUDED.adx,
                        dmp = EXCLUDED.dmp,
                        dmn = EXCLUDED.dmn,
                        hacim_orani = EXCLUDED.hacim_orani,
                        
                        signal = EXCLUDED.signal,
                        score = EXCLUDED.score,
                        stop_price = EXCLUDED.stop_price,
                        target_price = EXCLUDED.target_price,
                        macd_hist_onceki = EXCLUDED.macd_hist_onceki,
                        hacim_onceki = EXCLUDED.hacim_onceki,

                        fiyat_onceki = EXCLUDED.fiyat_onceki,
                        rsi_onceki = EXCLUDED.rsi_onceki,
                        adx_onceki = EXCLUDED.adx_onceki,
                        atr = EXCLUDED.atr,
                        
                        son_guncelleme = EXCLUDED.son_guncelleme,
                        strategy = EXCLUDED.strategy,

                        tags = EXCLUDED.tags,
                        main_strategy = EXCLUDED.main_strategy,
                        market_regime = EXCLUDED.market_regime,
                        confidence_score = EXCLUDED.confidence_score,

                        unified_score = EXCLUDED.unified_score,
                        conviction = EXCLUDED.conviction;";

                using (NpgsqlCommand cmd = new NpgsqlCommand(sql, conn))
                {
                    cmd.Parameters.AddWithValue("@sembol", hisse.Sembol);
                    cmd.Parameters.AddWithValue("@fiyat", hisse.Fiyat);
                    cmd.Parameters.AddWithValue("@sma50", hisse.Sma50);
                    cmd.Parameters.AddWithValue("@sma200", hisse.Sma200);
                    cmd.Parameters.AddWithValue("@fk", hisse.Fk);
                    cmd.Parameters.AddWithValue("@pd_dd", hisse.PdDd);
                    cmd.Parameters.AddWithValue("@rsi", hisse.Rsi);
                    cmd.Parameters.AddWithValue("@macd_line", hisse.MacdLine);
                    cmd.Parameters.AddWithValue("@macd_signal", hisse.MacdSignal);
                    cmd.Parameters.AddWithValue("@macd_hist", hisse.MacdHist);
                    cmd.Parameters.AddWithValue("@adx", hisse.Adx);
                    cmd.Parameters.AddWithValue("@dmp", hisse.Dmp);
                    cmd.Parameters.AddWithValue("@dmn", hisse.Dmn);
                    cmd.Parameters.AddWithValue("@hacim_orani", hisse.HacimOrani);
                    
                    cmd.Parameters.AddWithValue("@signal", hisse.Signal);
                    cmd.Parameters.AddWithValue("@score", hisse.Score);
                    cmd.Parameters.AddWithValue("@stop_price", hisse.StopPrice);
                    cmd.Parameters.AddWithValue("@target_price", hisse.TargetPrice);
                    cmd.Parameters.AddWithValue("@macd_hist_onceki", hisse.MacdHistOnceki);
                    cmd.Parameters.AddWithValue("@hacim_onceki", hisse.HacimOnceki);
                    
                    cmd.Parameters.AddWithValue("@fiyat_onceki", hisse.FiyatOnceki);
                    cmd.Parameters.AddWithValue("@rsi_onceki", hisse.RsiOnceki);
                    cmd.Parameters.AddWithValue("@adx_onceki", hisse.AdxOnceki);
                    cmd.Parameters.AddWithValue("@atr", hisse.Atr);
                    cmd.Parameters.AddWithValue("@strategy", hisse.Strategy);

                    // Pro Engine Params
                    cmd.Parameters.AddWithValue("@tags", (object)hisse.Tags ?? DBNull.Value);
                    cmd.Parameters.AddWithValue("@main_strategy", hisse.MainStrategy);
                    cmd.Parameters.AddWithValue("@market_regime", hisse.MarketRegime);
                    cmd.Parameters.AddWithValue("@confidence_score", hisse.ConfidenceScore);

                    // Unified Conviction Engine Params
                    cmd.Parameters.AddWithValue("@unified_score", hisse.UnifiedScore);
                    cmd.Parameters.AddWithValue("@conviction", hisse.Conviction);

                    cmd.ExecuteNonQuery();
                }
            }
        }

        public void KaydetSignalHistory(Hisse hisse)
        {
            using (NpgsqlConnection conn = new NpgsqlConnection(_connectionString))
            {
                conn.Open();

                // ── Duplicate Guard ───────────────────────────────────────────
                // Bugün aynı sembol + aynı sinyal zaten kaydedildiyse ekleme.
                string checkSql = @"
                    SELECT COUNT(*) FROM signal_history
                    WHERE sembol   = @sembol
                      AND signal   = @signal
                      AND signal_date::date = CURRENT_DATE";

                using (NpgsqlCommand checkCmd = new NpgsqlCommand(checkSql, conn))
                {
                    checkCmd.Parameters.AddWithValue("@sembol", hisse.Sembol);
                    checkCmd.Parameters.AddWithValue("@signal", hisse.Signal);
                    long count = (long)(checkCmd.ExecuteScalar() ?? 0L);
                    if (count > 0) return;   // Bugün zaten kaydedildi, atla
                }

                // ── Insert ────────────────────────────────────────────────────
                string sql = @"
                    INSERT INTO signal_history (
                        sembol, signal_date, signal, unified_score, conviction, score,
                        fiyat, stop_price, target_price,
                        rsi, adx, macd_hist,
                        market_regime, main_strategy, tags
                    ) VALUES (
                        @sembol, NOW(), @signal, @unified_score, @conviction, @score,
                        @fiyat, @stop_price, @target_price,
                        @rsi, @adx, @macd_hist,
                        @market_regime, @main_strategy, @tags
                    )";

                using (NpgsqlCommand cmd = new NpgsqlCommand(sql, conn))
                {
                    cmd.Parameters.AddWithValue("@sembol",        hisse.Sembol);
                    cmd.Parameters.AddWithValue("@signal",        hisse.Signal);
                    cmd.Parameters.AddWithValue("@unified_score", hisse.UnifiedScore);
                    cmd.Parameters.AddWithValue("@conviction",    hisse.Conviction);
                    cmd.Parameters.AddWithValue("@score",         hisse.Score);
                    cmd.Parameters.AddWithValue("@fiyat",         hisse.Fiyat);
                    cmd.Parameters.AddWithValue("@stop_price",    hisse.StopPrice);
                    cmd.Parameters.AddWithValue("@target_price",  hisse.TargetPrice);
                    cmd.Parameters.AddWithValue("@rsi",           hisse.Rsi);
                    cmd.Parameters.AddWithValue("@adx",           hisse.Adx);
                    cmd.Parameters.AddWithValue("@macd_hist",     hisse.MacdHist);
                    cmd.Parameters.AddWithValue("@market_regime", hisse.MarketRegime);
                    cmd.Parameters.AddWithValue("@main_strategy", hisse.MainStrategy);
                    cmd.Parameters.AddWithValue("@tags",          (object?)hisse.Tags ?? DBNull.Value);
                    cmd.ExecuteNonQuery();
                }
            }
        }


        public List<SignalHistory> GetSignalHistory(string? sembol, int limit)
        {
            var list = new List<SignalHistory>();
            using (NpgsqlConnection conn = new NpgsqlConnection(_connectionString))
            {
                conn.Open();
                string sql = string.IsNullOrEmpty(sembol)
                    ? $"SELECT * FROM signal_history ORDER BY signal_date DESC LIMIT @limit"
                    : $"SELECT * FROM signal_history WHERE sembol = @sembol ORDER BY signal_date DESC LIMIT @limit";

                using (NpgsqlCommand cmd = new NpgsqlCommand(sql, conn))
                {
                    cmd.Parameters.AddWithValue("@limit", limit);
                    if (!string.IsNullOrEmpty(sembol))
                        cmd.Parameters.AddWithValue("@sembol", sembol);

                    using (NpgsqlDataReader reader = cmd.ExecuteReader())
                    {
                        while (reader.Read())
                        {
                            var sh = new SignalHistory
                            {
                                Id          = reader.GetInt32(reader.GetOrdinal("id")),
                                Sembol      = reader.GetString(reader.GetOrdinal("sembol")),
                                SignalDate  = reader.GetDateTime(reader.GetOrdinal("signal_date")),
                                Signal      = reader.IsDBNull(reader.GetOrdinal("signal"))       ? "NO_TRADE" : reader.GetString(reader.GetOrdinal("signal")),
                                UnifiedScore= reader.IsDBNull(reader.GetOrdinal("unified_score"))? 0 : reader.GetInt32(reader.GetOrdinal("unified_score")),
                                Conviction  = reader.IsDBNull(reader.GetOrdinal("conviction"))   ? "BRONZE" : reader.GetString(reader.GetOrdinal("conviction")),
                                Score       = reader.IsDBNull(reader.GetOrdinal("score"))        ? 0 : reader.GetInt32(reader.GetOrdinal("score")),
                                Fiyat       = reader.IsDBNull(reader.GetOrdinal("fiyat"))        ? 0 : reader.GetDecimal(reader.GetOrdinal("fiyat")),
                                StopPrice   = reader.IsDBNull(reader.GetOrdinal("stop_price"))   ? 0 : reader.GetDecimal(reader.GetOrdinal("stop_price")),
                                TargetPrice = reader.IsDBNull(reader.GetOrdinal("target_price")) ? 0 : reader.GetDecimal(reader.GetOrdinal("target_price")),
                                Rsi         = reader.IsDBNull(reader.GetOrdinal("rsi"))          ? 0 : reader.GetDecimal(reader.GetOrdinal("rsi")),
                                Adx         = reader.IsDBNull(reader.GetOrdinal("adx"))          ? 0 : reader.GetDecimal(reader.GetOrdinal("adx")),
                                MacdHist    = reader.IsDBNull(reader.GetOrdinal("macd_hist"))    ? 0 : reader.GetDecimal(reader.GetOrdinal("macd_hist")),
                                MarketRegime= reader.IsDBNull(reader.GetOrdinal("market_regime"))? "SIDEWAYS" : reader.GetString(reader.GetOrdinal("market_regime")),
                                MainStrategy= reader.IsDBNull(reader.GetOrdinal("main_strategy"))? "NEUTRAL" : reader.GetString(reader.GetOrdinal("main_strategy")),
                                Tags        = reader.IsDBNull(reader.GetOrdinal("tags"))         ? Array.Empty<string>() : reader.GetFieldValue<string[]>(reader.GetOrdinal("tags")),
                                Fiyat1Gun   = reader.IsDBNull(reader.GetOrdinal("fiyat_1gun"))   ? null : reader.GetDecimal(reader.GetOrdinal("fiyat_1gun")),
                                Fiyat1Hafta = reader.IsDBNull(reader.GetOrdinal("fiyat_1hafta")) ? null : reader.GetDecimal(reader.GetOrdinal("fiyat_1hafta")),
                                Fiyat1Ay    = reader.IsDBNull(reader.GetOrdinal("fiyat_1ay"))    ? null : reader.GetDecimal(reader.GetOrdinal("fiyat_1ay")),
                                Perf1Gun    = reader.IsDBNull(reader.GetOrdinal("perf_1gun"))    ? null : reader.GetDecimal(reader.GetOrdinal("perf_1gun")),
                                Perf1Hafta  = reader.IsDBNull(reader.GetOrdinal("perf_1hafta"))  ? null : reader.GetDecimal(reader.GetOrdinal("perf_1hafta")),
                                Perf1Ay     = reader.IsDBNull(reader.GetOrdinal("perf_1ay"))     ? null : reader.GetDecimal(reader.GetOrdinal("perf_1ay")),
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
