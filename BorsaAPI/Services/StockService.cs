
using BorsaAPI.Models;

namespace BorsaAPI.Services
{
    public class StockService : IStockService
    {
        private readonly IStockRepository _stockRepository;

        public StockService(IStockRepository stockRepository)
        {
            _stockRepository = stockRepository;
        }

        public List<Stock> GetStocks(StockFilterDto filter)
        {
            return _stockRepository.GetAll(filter);
        }

        public List<Stock> GetTrendStocks()
        {
            return _stockRepository.GetAll(new StockFilterDto { Strategy = "TREND", MinScore = 65 });
        }

        public List<Stock> GetAllStocks()
        {
            return _stockRepository.GetAll(new StockFilterDto());
        }

        public List<Stock> GetTrendStocksWithFilters(StockFilterDto filter)
        {
            filter.Strategy = "TREND";
            filter.MinScore = filter.MinScore ?? 65;
            return _stockRepository.GetAll(filter);
        }

        public List<Stock> GetAllStocksWithFilters(StockFilterDto filter)
        {
            return _stockRepository.GetAll(filter);
        }
    }
}
