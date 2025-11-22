using BorsaAPI.Models;
using Npgsql;

namespace BorsaAPI.Services
{
    public class HisseRepository : IHisseRepository
    {
        private readonly string _connectionString;

        // Configuration'ı buraya inject ediyoruz (Constructor Injection)
        public HisseRepository(IConfiguration configuration)
        {
            _connectionString = configuration.GetConnectionString("BorsaDb")?? "";
        }

        public List<Hisse> TumHisseleriGetir()
        {
            List<Hisse> hisseListesi = new List<Hisse>();

            using (NpgsqlConnection conn = new NpgsqlConnection(_connectionString))
            {
                conn.Open();
                // F/K oranına göre sıralı getir
                string sql = "SELECT * FROM Hisseler ORDER BY fk ASC";

                using (NpgsqlCommand cmd = new NpgsqlCommand(sql, conn))
                {
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
                            
                            // Null kontrolü (Veri yoksa 0 dön)
                            hisse.Fk = reader.IsDBNull(reader.GetOrdinal("fk")) ? 0 : reader.GetDecimal(reader.GetOrdinal("fk"));
                            hisse.PdDd = reader.IsDBNull(reader.GetOrdinal("pd_dd")) ? 0 : reader.GetDecimal(reader.GetOrdinal("pd_dd"));
                            
                            hisse.SonGuncelleme = reader.GetDateTime(reader.GetOrdinal("son_guncelleme"));

                            hisseListesi.Add(hisse);
                        }
                    }
                }
            }
            return hisseListesi;
        }
    }
}