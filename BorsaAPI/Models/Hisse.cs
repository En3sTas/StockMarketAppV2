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
        public decimal MacdLine { get; set; }
        public decimal MacdSignal { get; set; }
        public decimal MacdHist { get; set; }
        public decimal BuyumeOrani { get; set; }
        public decimal Adx { get; set; }
        public decimal Dmp { get; set; }
        public decimal Dmn { get; set; }
        public decimal HacimOrani { get; set; }
        public DateTime SonGuncelleme { get; set; }
    }
}