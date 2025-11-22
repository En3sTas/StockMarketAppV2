using BorsaAPI.Models;

namespace BorsaAPI.Services
{
    // Bu arayüz, yapılacak işlerin listesidir (Menü)
    public interface IHisseRepository
    {
        List<Hisse> TumHisseleriGetir();
    }
}