using BorsaAPI.Models;

namespace BorsaAPI.Services
{
    public interface IHisseRepository
    {
        List<Hisse> TumHisseleriGetir(
            HisselerFilterDto filter);

        void Kaydet(Hisse hisse);
    }
}