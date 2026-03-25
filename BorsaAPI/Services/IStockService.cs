using BorsaAPI.Models;

namespace BorsaAPI.Services
{
    public interface IStockService
    {
        List<Stock> GetStocks(StockFilterDto filter);
        List<Stock> GetTrendStocks();
        List<Stock> GetAllStocks();

        // Methods that accept user filters
        List<Stock> GetTrendStocksWithFilters(StockFilterDto filter);
        List<Stock> GetAllStocksWithFilters(StockFilterDto filter);
    }
}
