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
        public IActionResult GetTrend()
        {
            // Business logic moved to Service
            return Ok(_hisseService.GetTrendStocks());
        }

        [HttpGet("/api/market/scout")]
        public IActionResult GetScout()
        {
             // Business logic moved to Service
            return Ok(_hisseService.GetScoutStocks());
        }

        [HttpGet("/api/market/all")]
        public IActionResult GetAllStocks()
        {
             // Business logic moved to Service
            return Ok(_hisseService.GetAllStocks());
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