// HisseRepository.cs - FİNAL VERSİYON
using BorsaAPI.Models;
using Npgsql;
using System.Text; // StringBuilder için gerekli

namespace BorsaAPI.Services
{
    public class HisseRepository : IHisseRepository
    {
        private readonly string _connectionString;

        public HisseRepository(IConfiguration configuration)
        {
            // Veritabanı bağlantı cümleciğini alıyoruz
            _connectionString = configuration.GetConnectionString("BorsaDb") ?? string.Empty;
        }

        public List<Hisse> TumHisseleriGetir(decimal? maxFk, decimal? minFk,
                                             decimal? maxPdDd, decimal? minPdDd,
                                             decimal? maxRsi, decimal? minRsi,
                                             decimal? maxMacdLine, decimal? minMacdLine,
                                             decimal? maxMacdSignal, decimal? minMacdSignal,
                                             decimal? maxMacdHist, decimal? minMacdHist,
                                             decimal? maxBuyumeOrani, decimal? minBuyumeOrani)
        {
            List<Hisse> hisseListesi = new List<Hisse>();

            using (NpgsqlConnection conn = new NpgsqlConnection(_connectionString))
            {
                conn.Open();

                // 1. DİNAMİK SQL İNŞASI
                // "WHERE 1=1" taktiği: İlk koşul her zaman doğrudur, böylece sonraki her filtre için başına "AND" koyabiliriz.
                StringBuilder sqlBuilder = new StringBuilder("SELECT * FROM Hisseler WHERE 1=1");
                
                NpgsqlCommand cmd = new NpgsqlCommand();
                cmd.Connection = conn;

                // --- 2. KOŞULLARI EKLE (TÜM FİLTRELER) ---

                // F/K Filtresi
                if (minFk.HasValue)
                {
                    sqlBuilder.Append(" AND fk >= @minFk");
                    cmd.Parameters.AddWithValue("@minFk", minFk.Value);
                }
                if (maxFk.HasValue)
                {
                    sqlBuilder.Append(" AND fk <= @maxFk");
                    cmd.Parameters.AddWithValue("@maxFk", maxFk.Value);
                }

                // PD/DD Filtresi
                if (minPdDd.HasValue)
                {
                    sqlBuilder.Append(" AND pd_dd >= @minPdDd");
                    cmd.Parameters.AddWithValue("@minPdDd", minPdDd.Value);
                }
                if (maxPdDd.HasValue)
                {
                    sqlBuilder.Append(" AND pd_dd <= @maxPdDd");
                    cmd.Parameters.AddWithValue("@maxPdDd", maxPdDd.Value);
                }
                
                // RSI Filtresi
                if (minRsi.HasValue)
                {
                    sqlBuilder.Append(" AND rsi >= @minRsi");
                    cmd.Parameters.AddWithValue("@minRsi", minRsi.Value);
                }
                if (maxRsi.HasValue)
                {
                    sqlBuilder.Append(" AND rsi <= @maxRsi");
                    cmd.Parameters.AddWithValue("@maxRsi", maxRsi.Value);
                }

                // MACD Histogram Filtresi (En sık kullanılan)
                if (minMacdHist.HasValue)
                {
                    sqlBuilder.Append(" AND macd_hist >= @minMacdHist");
                    cmd.Parameters.AddWithValue("@minMacdHist", minMacdHist.Value);
                }
                if (maxMacdHist.HasValue)
                {
                    sqlBuilder.Append(" AND macd_hist <= @maxMacdHist");
                    cmd.Parameters.AddWithValue("@maxMacdHist", maxMacdHist.Value);
                }

                // MACD Line Filtresi
                if (minMacdLine.HasValue)
                {
                    sqlBuilder.Append(" AND macd_line >= @minMacdLine");
                    cmd.Parameters.AddWithValue("@minMacdLine", minMacdLine.Value);
                }
                if (maxMacdLine.HasValue)
                {
                    sqlBuilder.Append(" AND macd_line <= @maxMacdLine");
                    cmd.Parameters.AddWithValue("@maxMacdLine", maxMacdLine.Value);
                }

                // MACD Signal Filtresi
                if (minMacdSignal.HasValue)
                {
                    sqlBuilder.Append(" AND macd_signal >= @minMacdSignal");
                    cmd.Parameters.AddWithValue("@minMacdSignal", minMacdSignal.Value);
                }
                if (maxMacdSignal.HasValue)
                {
                    sqlBuilder.Append(" AND macd_signal <= @maxMacdSignal");
                    cmd.Parameters.AddWithValue("@maxMacdSignal", maxMacdSignal.Value);
                }

                // Büyüme Oranı Filtresi
                if (minBuyumeOrani.HasValue)
                {
                    sqlBuilder.Append(" AND buyume_orani >= @minBuyumeOrani");
                    cmd.Parameters.AddWithValue("@minBuyumeOrani", minBuyumeOrani.Value);
                }
                if (maxBuyumeOrani.HasValue)
                {
                    sqlBuilder.Append(" AND buyume_orani <= @maxBuyumeOrani");
                    cmd.Parameters.AddWithValue("@maxBuyumeOrani", maxBuyumeOrani.Value);
                }

                // 3. SIRALAMA (Alfabetik)
                sqlBuilder.Append(" ORDER BY sembol ASC");

                // 4. SORGUEYU ÇALIŞTIR
                cmd.CommandText = sqlBuilder.ToString();

                using (NpgsqlDataReader reader = cmd.ExecuteReader())
                {
                    while (reader.Read())
                    {
                        Hisse hisse = new Hisse();
                        
                        // ID ve Sembol
                        hisse.Id = reader.GetInt32(reader.GetOrdinal("id"));
                        hisse.Sembol = reader.GetString(reader.GetOrdinal("sembol"));
                        
                        // Temel Veriler
                        hisse.Fiyat = reader.GetDecimal(reader.GetOrdinal("fiyat"));
                        hisse.Sma50 = reader.GetDecimal(reader.GetOrdinal("sma_50"));
                        hisse.Sma200 = reader.GetDecimal(reader.GetOrdinal("sma_200"));
                        
                        // İndikatörler (Null kontrolü - Veritabanında boşsa 0 ata)
                        hisse.Rsi = reader.IsDBNull(reader.GetOrdinal("rsi")) ? 0 : reader.GetDecimal(reader.GetOrdinal("rsi"));
                        hisse.Fk = reader.IsDBNull(reader.GetOrdinal("fk")) ? 0 : reader.GetDecimal(reader.GetOrdinal("fk"));
                        hisse.PdDd = reader.IsDBNull(reader.GetOrdinal("pd_dd")) ? 0 : reader.GetDecimal(reader.GetOrdinal("pd_dd"));
                        
                        hisse.MacdLine = reader.IsDBNull(reader.GetOrdinal("macd_line")) ? 0 : reader.GetDecimal(reader.GetOrdinal("macd_line"));
                        hisse.MacdSignal = reader.IsDBNull(reader.GetOrdinal("macd_signal")) ? 0 : reader.GetDecimal(reader.GetOrdinal("macd_signal"));
                        hisse.MacdHist = reader.IsDBNull(reader.GetOrdinal("macd_hist")) ? 0 : reader.GetDecimal(reader.GetOrdinal("macd_hist"));
                        
                        hisse.BuyumeOrani = reader.IsDBNull(reader.GetOrdinal("buyume_orani")) ? 0 : reader.GetDecimal(reader.GetOrdinal("buyume_orani"));
                        
                        // Tarih
                        hisse.SonGuncelleme = reader.GetDateTime(reader.GetOrdinal("son_guncelleme"));

                        hisseListesi.Add(hisse);
                    }
                }
            }
            return hisseListesi;
        }
    }
}