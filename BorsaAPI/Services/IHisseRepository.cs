using BorsaAPI.Models;

namespace BorsaAPI.Services
{
    
    public interface IHisseRepository
    {
        List<Hisse> TumHisseleriGetir(
            decimal? maxFk,decimal? minFk,
            decimal? maxPdDd,decimal? minPdDd,
            decimal? maxRsi, decimal? minRsi);

        
    }
}