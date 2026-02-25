using BorsaAPI.Models;

namespace BorsaAPI.Services
{
    public interface IHisseService
    {
        List<Hisse> GetHisseler(HisselerFilterDto filter);
        List<Hisse> GetTrendStocks();
        List<Hisse> GetAllStocks();
        
        // Methods that accept user filters
        List<Hisse> GetTrendStocksWithFilters(HisselerFilterDto filter);
        List<Hisse> GetAllStocksWithFilters(HisselerFilterDto filter);
    }
}
