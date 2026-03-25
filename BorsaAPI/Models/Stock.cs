
namespace BorsaAPI.Models
{
    public class Stock
    {
        public int Id { get; set; }
        public string Symbol { get; set; } = string.Empty;
        public decimal Price { get; set; }
        public decimal Sma50 { get; set; }
        public decimal Sma200 { get; set; }
        public decimal PeRatio { get; set; }
        public decimal PbRatio { get; set; }
        public decimal Rsi { get; set; }
        public decimal MacdLine { get; set; }
        public decimal MacdSignal { get; set; }
        public decimal MacdHist { get; set; }
        public decimal Adx { get; set; }
        public decimal Dmp { get; set; }
        public decimal Dmn { get; set; }
        public decimal VolumeRatio { get; set; }
        public DateTime LastUpdated { get; set; }
        public decimal PricePrev { get; set; }
        public decimal RsiPrev { get; set; }
        public decimal AdxPrev { get; set; }
        public string Signal { get; set; } = "NO_TRADE";
        public int Score { get; set; }
        public decimal StopPrice { get; set; }
        public decimal TargetPrice { get; set; }
        public decimal MacdHistPrev { get; set; }
        public decimal VolumePrev { get; set; }
        public decimal Atr { get; set; }
        public string Strategy { get; set; } = "NONE";

        // Extended Fields (Pro Engine)
        public string[] Tags { get; set; } = Array.Empty<string>();
        public string MainStrategy { get; set; } = "NEUTRAL";
        public string MarketRegime { get; set; } = "SIDEWAYS";
        public int ConfidenceScore { get; set; } = 0;

        // Unified Conviction Engine
        public int UnifiedScore { get; set; } = 0;
        public string Conviction { get; set; } = "BRONZE";
    }
}
