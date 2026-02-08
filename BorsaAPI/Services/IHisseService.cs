using BorsaAPI.Models;

namespace BorsaAPI.Services
{
    public interface IHisseService
    {
        List<Hisse> GetHisseler(HisselerFilterDto filter);
        List<Hisse> GetTrendStocks();
        List<Hisse> GetScoutStocks();
        List<Hisse> GetAllStocks();
    }
}
