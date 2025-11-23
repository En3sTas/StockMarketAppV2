using BorsaAPI.Models;

namespace BorsaAPI.Services
{
    
    public interface IHisseRepository
    {
        List<Hisse> TumHisseleriGetir(
            decimal? maxFk,decimal? minFk,
            decimal? maxPdDd,decimal? minPdDd,
            decimal? maxRsi, decimal? minRsi,
            decimal? maxMacdLine, decimal? minMacdLine,
            decimal? maxMacdSignal, decimal? minMacdSignal,
            decimal? maxMacdHist, decimal? minMacdHist,
            decimal? maxBuyumeOrani, decimal? minBuyumeOrani,
            decimal? maxAdx, decimal? minAdx,
            decimal? maxDmp, decimal? minDmp,   
            decimal? maxDmn, decimal? minDmn,
            decimal? maxHacimOrani, decimal? minHacimOrani);
            
        
    }
}