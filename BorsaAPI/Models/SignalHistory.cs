
namespace BorsaAPI.Models
{
    public class SignalHistory
    {
        public int Id { get; set; }
        public string Symbol { get; set; } = string.Empty;
        public DateTime SignalDate { get; set; }

        // Signal Info
        public string Signal { get; set; } = "NO_TRADE";
        public int UnifiedScore { get; set; } = 0;
        public string Conviction { get; set; } = "BRONZE";
        public int Score { get; set; } = 0;

        // Price at Signal Time
        public decimal Price { get; set; }
        public decimal StopPrice { get; set; }
        public decimal TargetPrice { get; set; }

        // Indicators at Signal Time (Trend Hunter)
        public decimal Rsi { get; set; }
        public decimal Adx { get; set; }
        public decimal MacdHist { get; set; }

        // Market Context (Smart Picks)
        public string MarketRegime { get; set; } = "SIDEWAYS";
        public string MainStrategy { get; set; } = "NEUTRAL";
        public string[] Tags { get; set; } = Array.Empty<string>();

        // Future Price Tracking (auto-filled by Python worker)
        public decimal? Price1Day { get; set; }
        public decimal? Price1Week { get; set; }
        public decimal? Price1Month { get; set; }

        // Performance %
        public decimal? Perf1Day { get; set; }
        public decimal? Perf1Week { get; set; }
        public decimal? Perf1Month { get; set; }
    }
}
