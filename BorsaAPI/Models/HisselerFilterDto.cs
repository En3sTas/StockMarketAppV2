namespace BorsaAPI.Models
{
    public class HisselerFilterDto
    {
        public decimal? MaxFk { get; set; }
        public decimal? MinFk { get; set; }
        public decimal? MaxPdDd { get; set; }
        public decimal? MinPdDd { get; set; }
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
        public decimal? MaxHacimOrani { get; set; }
        public decimal? MinHacimOrani { get; set; }
        public string? Signal { get; set; }
        public string? Strategy { get; set; }
        public int? MinScore { get; set; }
    }
}
