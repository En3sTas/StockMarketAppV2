
using Microsoft.AspNetCore.Mvc;
using BorsaAPI.Models;
using BorsaAPI.Services;
using Microsoft.AspNetCore.SignalR;
using BorsaAPI.Hubs;

namespace BorsaAPI.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class StocksController : ControllerBase
    {
        private readonly IStockService _stockService;
        private readonly IHubContext<BorsaHub> _hubContext;

        public StocksController(IStockService stockService, IHubContext<BorsaHub> hubContext)
        {
            _stockService = stockService;
            _hubContext = hubContext;
        }

        // GET /api/stocks — General endpoint with filters
        [HttpGet]
        public IActionResult GetStocks([FromQuery] StockFilterDto filter)
        {
            try
            {
                var stocks = _stockService.GetStocks(filter);
                return Ok(stocks);
            }
            catch (Exception ex)
            {
                return StatusCode(500, "Error: " + ex.Message);
            }
        }

        // GET /api/market/trend
        [HttpGet("/api/market/trend")]
        public IActionResult GetTrend([FromQuery] StockFilterDto filter)
        {
            return Ok(_stockService.GetTrendStocksWithFilters(filter));
        }

        // GET /api/market/all
        [HttpGet("/api/market/all")]
        public IActionResult GetAll([FromQuery] StockFilterDto filter)
        {
            return Ok(_stockService.GetAllStocksWithFilters(filter));
        }

        // POST /api/market/notify — Internal: broadcast a stock update via SignalR
        [HttpPost("/api/market/notify")]
        public async Task<IActionResult> NotifyUpdate([FromBody] Stock stock)
        {
            if (stock == null) return BadRequest("Invalid payload.");
            await _hubContext.Clients.All.SendAsync("ReceiveStockUpdate", stock);
            return Ok(new { status = "Broadcasted", symbol = stock.Symbol });
        }

        // GET /api/signals/history
        [HttpGet("/api/signals/history")]
        public IActionResult GetSignalHistory([FromQuery] string? symbol, [FromQuery] int limit = 50)
        {
            try
            {
                var repository = HttpContext.RequestServices.GetRequiredService<IStockRepository>();
                var history = repository.GetSignalHistory(symbol, limit);
                return Ok(history);
            }
            catch (Exception ex)
            {
                return StatusCode(500, "Error: " + ex.Message);
            }
        }
    }
}
