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

        public List<Hisse> TumHisseleriGetir(decimal? maxFk, decimal? minFk,
                                             decimal? maxPdDd, decimal? minPdDd,
                                             decimal? maxRsi, decimal? minRsi,
                                             decimal? maxMacdLine, decimal? minMacdLine,
                                             decimal? maxMacdSignal, decimal? minMacdSignal,
                                             decimal? maxMacdHist, decimal? minMacdHist,
                                             
                                             decimal? maxAdx, decimal? minAdx,
                                             decimal? maxDmp, decimal? minDmp,
                                             decimal? maxDmn, decimal? minDmn
                                             ,decimal? maxHacimOrani, decimal? minHacimOrani)
        {
            List<Hisse> hisseListesi = new List<Hisse>();

            using (NpgsqlConnection conn = new NpgsqlConnection(_connectionString))
            {
                conn.Open();
                StringBuilder sqlBuilder = new StringBuilder("SELECT * FROM Hisseler WHERE 1=1");
                NpgsqlCommand cmd = new NpgsqlCommand();
                cmd.Connection = conn;

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
                if (minAdx.HasValue)
                {
                    sqlBuilder.Append(" AND adx >= @minAdx");
                    cmd.Parameters.AddWithValue("@minAdx", minAdx.Value);
                }   
                if (maxAdx.HasValue)
                {
                    sqlBuilder.Append(" AND adx <= @maxAdx");
                    cmd.Parameters.AddWithValue("@maxAdx", maxAdx.Value);
                }
                if (minDmp.HasValue)
                {
                    sqlBuilder.Append(" AND dmp >= @minDmp");
                    cmd.Parameters.AddWithValue("@minDmp", minDmp.Value);
                }
                if (maxDmp.HasValue)
                {
                    sqlBuilder.Append(" AND dmp <= @maxDmp");
                    cmd.Parameters.AddWithValue("@maxDmp", maxDmp.Value);
                }
                if (minDmn.HasValue)
                {
                    sqlBuilder.Append(" AND dmn >= @minDmn");
                    cmd.Parameters.AddWithValue("@minDmn", minDmn.Value);
                }
                if (maxDmn.HasValue)
                {
                    sqlBuilder.Append(" AND dmn <= @maxDmn");
                    cmd.Parameters.AddWithValue("@maxDmn", maxDmn.Value);
                }
                if (minHacimOrani.HasValue)
                {
                    sqlBuilder.Append(" AND hacim_orani >= @minHacimOrani");
                    cmd.Parameters.AddWithValue("@minHacimOrani", minHacimOrani.Value);
                }
                if (maxHacimOrani.HasValue)
                {
                    sqlBuilder.Append(" AND hacim_orani <= @maxHacimOrani");
                    cmd.Parameters.AddWithValue("@maxHacimOrani", maxHacimOrani.Value);
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
                        
                        hisse.MacdLine = reader.IsDBNull(reader.GetOrdinal("macd_line")) ? 0 : reader.GetDecimal(reader.GetOrdinal("macd_line"));
                        hisse.MacdSignal = reader.IsDBNull(reader.GetOrdinal("macd_signal")) ? 0 : reader.GetDecimal(reader.GetOrdinal("macd_signal"));
                        hisse.MacdHist = reader.IsDBNull(reader.GetOrdinal("macd_hist")) ? 0 : reader.GetDecimal(reader.GetOrdinal("macd_hist"));
                        
                        hisse.Adx = reader.IsDBNull(reader.GetOrdinal("adx")) ? 0 : reader.GetDecimal(reader.GetOrdinal("adx"));
                        hisse.Dmp = reader.IsDBNull(reader.GetOrdinal("dmp")) ? 0 : reader.GetDecimal(reader.GetOrdinal("dmp"));
                        hisse.Dmn = reader.IsDBNull(reader.GetOrdinal("dmn")) ? 0 : reader.GetDecimal(reader.GetOrdinal("dmn"));

                        hisse.HacimOrani = reader.IsDBNull(reader.GetOrdinal("hacim_orani")) ? 0 : reader.GetDecimal(reader.GetOrdinal("hacim_orani"));
                        hisse.SonGuncelleme = reader.GetDateTime(reader.GetOrdinal("son_guncelleme"));

                        hisseListesi.Add(hisse);
                    }
                }
            }
            return hisseListesi;
        }
    }
}