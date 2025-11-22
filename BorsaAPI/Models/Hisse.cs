namespace BorsaAPI.Models
{
    public class Hisse
    {
        public int Id { get; set; }
        public string Sembol { get; set; } = string.Empty;
        public decimal Fiyat { get; set; }
        public decimal Sma50 { get; set; }
        public decimal Sma200 { get; set; }
        public decimal Fk { get; set; }
        public decimal PdDd { get; set; }
        public decimal Rsi {get;set;}
        public DateTime SonGuncelleme { get; set; }
    }
}