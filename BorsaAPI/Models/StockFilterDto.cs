namespace BorsaAPI.Models
{
    public class StockFilterDto
    {
        public decimal? MaxPeRatio { get; set; }
        public decimal? MinPeRatio { get; set; }
        public decimal? MaxPbRatio { get; set; }
        public decimal? MinPbRatio { get; set; }
        public decimal? MaxRsi { get; set; }
        public decimal? MinRsi { get; set; }
        public decimal? MaxMacdLine { get; set; }
        public decimal? MinMacdLine { get; set; }
        public decimal? MaxMacdSignal { get; set; }
        public decimal? MinMacdSignal { get; set; }
        public decimal? MaxMacdHist { get; set; }
        public decimal? MinMacdHist { get; set; }
        public decimal? MaxAdx { get; set; }
        public decimal? MinAdx { get; set; }
        public decimal? MaxDmp { get; set; }
        public decimal? MinDmp { get; set; }
        public decimal? MaxDmn { get; set; }
        public decimal? MinDmn { get; set; }
        public decimal? MaxVolumeRatio { get; set; }
        public decimal? MinVolumeRatio { get; set; }
        public string? Signal { get; set; }
        public string? Strategy { get; set; }
        public int? MinScore { get; set; }
    }
}
