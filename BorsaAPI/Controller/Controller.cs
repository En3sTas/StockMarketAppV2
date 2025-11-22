using Microsoft.AspNetCore.Mvc;
using BorsaAPI.Models;
using BorsaAPI.Services; // <-- Using değişti

namespace BorsaAPI.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class HisselerController : ControllerBase
    {
        private readonly IHisseRepository _hisseRepository; // <-- Değişken adı değişti

        // Constructor Injection
        public HisselerController(IHisseRepository hisseRepository)
        {
            _hisseRepository = hisseRepository;
        }

        [HttpGet]
        public IActionResult GetHisseler()
        {
            try
            {
                // Service üzerinden veriyi çekiyoruz
                var veriler = _hisseRepository.TumHisseleriGetir();
                return Ok(veriler);
            }
            catch (Exception ex)
            {
                return StatusCode(500, "Hata: " + ex.Message);
            }
        }
    }
}