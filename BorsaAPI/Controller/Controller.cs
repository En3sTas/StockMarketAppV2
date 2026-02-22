
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
        private readonly IHisseService _hisseService;
        private readonly IHubContext<BorsaHub> _hubContext;

        public HisselerController(IHisseService hisseService, IHubContext<BorsaHub> hubContext)
        {
            _hisseService = hisseService;
            _hubContext = hubContext;
        }

        [HttpGet]
        public IActionResult GetHisseler([FromQuery] HisselerFilterDto filter)
        {
            try
            {
                var veriler = _hisseService.GetHisseler(filter);
                return Ok(veriler);
            }
            catch (Exception ex)
            {
                return StatusCode(500, "Error: " + ex.Message);
            }
        }

        [HttpGet("/api/market/trend")]
        public IActionResult GetTrend([FromQuery] HisselerFilterDto filter)
        {
            return Ok(_hisseService.GetTrendStocksWithFilters(filter));
        }

        [HttpGet("/api/market/scout")]
        public IActionResult GetScout([FromQuery] HisselerFilterDto filter)
        {
            return Ok(_hisseService.GetScoutStocksWithFilters(filter));
        }

        [HttpGet("/api/market/all")]
        public IActionResult GetAllStocks([FromQuery] HisselerFilterDto filter)
        {
            return Ok(_hisseService.GetAllStocksWithFilters(filter));
        }

        [HttpPost("/api/market/notify")]
        public async Task<IActionResult> NotifyUpdate([FromBody] Hisse hisse)
        {
            if (hisse == null) return BadRequest("Invalid Data");

            // Real-time Update via SignalR
            await _hubContext.Clients.All.SendAsync("ReceiveStockUpdate", hisse);

            return Ok(new { status = "Broadcasted", symbol = hisse.Sembol });
        }
    }
}