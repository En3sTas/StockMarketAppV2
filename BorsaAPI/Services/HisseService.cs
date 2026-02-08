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
            // TREND + SCORE > 65
            return _hisseRepository.TumHisseleriGetir(new HisselerFilterDto { Strategy = "TREND", MinScore = 65 });
        }

        public List<Hisse> GetScoutStocks()
        {
            // SCOUT + SCORE > 65
            return _hisseRepository.TumHisseleriGetir(new HisselerFilterDto { Strategy = "SCOUT", MinScore = 65 });
        }

        public List<Hisse> GetAllStocks()
        {
            // ALL STOCKS (No Strategy Filter, No Score Filter)
            return _hisseRepository.TumHisseleriGetir(new HisselerFilterDto());
        }
    }
}
