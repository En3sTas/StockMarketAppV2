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
            [FromQuery] decimal? minRsi,
            [FromQuery] decimal? maxRsi,
            [FromQuery] decimal? minMacdLine, [FromQuery] decimal? maxMacdLine,     
            [FromQuery] decimal? minMacdSignal, [FromQuery] decimal? maxMacdSignal, 
            [FromQuery] decimal? minMacdHist, [FromQuery] decimal? maxMacdHist  
            )
        {
            try
            {
                
                var veriler = _hisseRepository.TumHisseleriGetir(maxFk, minFk, 
                                                                 maxPdDd, minPdDd,
                                                                 maxRsi,minRsi,
                                                                 minMacdLine, maxMacdLine,
                                                                 minMacdSignal, maxMacdSignal,
                                                                 minMacdHist, maxMacdHist);
                return Ok(veriler);
            }
            catch (Exception ex)
            {
                return StatusCode(500, "Hata: " + ex.Message);
            }
        }
    }
}