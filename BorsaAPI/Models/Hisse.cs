
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
        public decimal Adx { get; set; }
        public decimal Dmp { get; set; }
        public decimal Dmn { get; set; }
        public decimal HacimOrani { get; set; }
        public DateTime SonGuncelleme { get; set; }
        public decimal FiyatOnceki { get; set; }
        public decimal RsiOnceki { get; set; }
        public decimal AdxOnceki { get; set; }
        public string Signal { get; set; } = "NO_TRADE";
        public int Score { get; set; }
        public decimal StopPrice { get; set; }
        public decimal TargetPrice { get; set; }
        public decimal MacdHistOnceki { get; set; }
        public decimal HacimOnceki { get; set; }
        public decimal Atr { get; set; }
        public string Strategy { get; set; } = "NONE";
        
        // Extended Fields (Pro Engine)
        public string[] Tags { get; set; } = Array.Empty<string>();
        public string MainStrategy { get; set; } = "NEUTRAL";
        public string MarketRegime { get; set; } = "SIDEWAYS";
        public int ConfidenceScore { get; set; } = 0;
    }
}