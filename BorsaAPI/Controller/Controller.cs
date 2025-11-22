using Microsoft.AspNetCore.Mvc;
using BorsaAPI.Models;
using BorsaAPI.Services; // <-- Using değişti

namespace BorsaAPI.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class HisselerController : ControllerBase
    {
        private readonly IHisseRepository _hisseRepository; 

        
        public HisselerController(IHisseRepository hisseRepository)
        {
            _hisseRepository = hisseRepository;
        }

        [HttpGet]
        public IActionResult GetHisseler([FromQuery] decimal? maxFk, 
            [FromQuery] decimal? minFk, 
            [FromQuery] decimal? maxPdDd, 
            [FromQuery] decimal? minPdDd,
            [FromQuery] decimal? maxRsi,
            [FromQuery] decimal? minRsi,
            [FromQuery] decimal? maxMacdLine,
            [FromQuery] decimal? minMacdLine, 
            [FromQuery] decimal? maxMacdSignal,      
            [FromQuery] decimal? minMacdSignal, 
            [FromQuery] decimal? maxMacdHist,
            [FromQuery] decimal? minMacdHist,
            [FromQuery] decimal? maxBuyumeOrani,
            [FromQuery] decimal? minBuyumeOrani
            )
        {
            try
            {
                
                var veriler = _hisseRepository.TumHisseleriGetir(maxFk, minFk, 
                                                                 maxPdDd, minPdDd,
                                                                 maxRsi,minRsi,
                                                                 maxMacdLine, minMacdLine,
                                                                 maxMacdSignal, minMacdSignal,
                                                                 maxMacdHist, minMacdHist,
                                                                 maxBuyumeOrani,minBuyumeOrani);
                return Ok(veriler);
            }
            catch (Exception ex)
            {
                return StatusCode(500, "Hata: " + ex.Message);
            }
        }
    }
}