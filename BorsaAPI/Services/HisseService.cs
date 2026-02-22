
using BorsaAPI.Models;

namespace BorsaAPI.Services
{
    public class HisseService : IHisseService
    {
        private readonly IHisseRepository _hisseRepository;

        public HisseService(IHisseRepository hisseRepository)
        {
            _hisseRepository = hisseRepository;
        }

        public List<Hisse> GetHisseler(HisselerFilterDto filter)
        {
            return _hisseRepository.TumHisseleriGetir(filter);
        }

        public List<Hisse> GetTrendStocks()
        {
            // Default Trend Filter (Score > 65)
            return _hisseRepository.TumHisseleriGetir(new HisselerFilterDto { Strategy = "TREND", MinScore = 65 });
        }

        public List<Hisse> GetScoutStocks()
        {
            // Default Scout Filter (Score > 65)
            return _hisseRepository.TumHisseleriGetir(new HisselerFilterDto { Strategy = "SCOUT", MinScore = 65 });
        }

        public List<Hisse> GetAllStocks()
        {
            return _hisseRepository.TumHisseleriGetir(new HisselerFilterDto());
        }

        public List<Hisse> GetTrendStocksWithFilters(HisselerFilterDto filter)
        {
            // Force TREND strategy + Merge Filters
            filter.Strategy = "TREND";
            filter.MinScore = filter.MinScore ?? 65; 
            return _hisseRepository.TumHisseleriGetir(filter);
        }

        public List<Hisse> GetScoutStocksWithFilters(HisselerFilterDto filter)
        {
            // Force SCOUT strategy + Merge Filters
            filter.Strategy = "SCOUT";
            filter.MinScore = filter.MinScore ?? 65; 
            return _hisseRepository.TumHisseleriGetir(filter);
        }

        public List<Hisse> GetAllStocksWithFilters(HisselerFilterDto filter)
        {
            return _hisseRepository.TumHisseleriGetir(filter);
        }
    }
}
