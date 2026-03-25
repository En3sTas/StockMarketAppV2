using BorsaAPI.Models;

namespace BorsaAPI.Services
{
    public interface IStockRepository
    {
        List<Stock> GetAll(StockFilterDto filter);
        void Save(Stock stock);

        // Signal History
        void SaveSignalHistory(Stock stock);
        List<SignalHistory> GetSignalHistory(string? symbol, int limit);
    }
}
