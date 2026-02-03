using Microsoft.AspNetCore.Mvc;
using BorsaAPI.Models;
using BorsaAPI.Services;
using Microsoft.AspNetCore.SignalR;
using BorsaAPI.Hubs;
using System.Threading.Tasks;

namespace BorsaAPI.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class HisselerController : ControllerBase
    {
        private readonly IHisseRepository _hisseRepository;
        private readonly IHubContext<BorsaHub> _hubContext;

        public HisselerController(IHisseRepository hisseRepository, IHubContext<BorsaHub> hubContext)
        {
            _hisseRepository = hisseRepository;
            _hubContext = hubContext;
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
            
            [FromQuery] decimal? maxAdx,
            [FromQuery] decimal? minAdx,
            [FromQuery] decimal? maxDmp,
            [FromQuery] decimal? minDmp,
            [FromQuery] decimal? maxDmn,
            [FromQuery] decimal? minDmn,
            [FromQuery] decimal? maxHacimOrani,
            [FromQuery] decimal? minHacimOrani,
            [FromQuery] string? signal,
            [FromQuery] string? strategy,
            [FromQuery] int? minScore)
        {
            try
            {
                var veriler = _hisseRepository.TumHisseleriGetir(maxFk, minFk, 
                                                                 maxPdDd, minPdDd,
                                                                 maxRsi,minRsi,
                                                                 maxMacdLine, minMacdLine,
                                                                 maxMacdSignal, minMacdSignal,
                                                                 maxMacdHist, minMacdHist,
                                                                 
                                                                 maxAdx, minAdx,
                                                                 maxDmp, minDmp,
                                                                 maxDmn, minDmn,
                                                                 maxHacimOrani, minHacimOrani, signal, strategy, minScore);
                return Ok(veriler);
            }
            catch (Exception ex)
            {
                return StatusCode(500, "Error: " + ex.Message);
            }
        }

        [HttpGet("/api/market/trend")]
        public IActionResult GetTrend()
        {
            // TREND + SCORE > 65
            return GetHisseler(null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null, "TREND", 65);
        }

        [HttpGet("/api/market/scout")]
        public IActionResult GetScout()
        {
             // SCOUT + SCORE > 65
            return GetHisseler(null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null, "SCOUT", 65);
        }

        [HttpGet("/api/market/all")]
        public IActionResult GetAllStocks()
        {
             // ALL STOCKS (No Strategy Filter, No Score Filter)
            return GetHisseler(null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null, null, null);
        }

        [HttpPost("/api/market/notify")]
        public async Task<IActionResult> NotifyUpdate([FromBody] Hisse hisse)
        {
            if (hisse == null) return BadRequest("Invalid Data");

            // Broadcast to all connected clients
            await _hubContext.Clients.All.SendAsync("ReceiveStockUpdate", hisse);

            return Ok(new { status = "Broadcasted", symbol = hisse.Sembol });
        }
    }
}