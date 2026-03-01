using BorsaAPI.Models;

namespace BorsaAPI.Services
{
    public interface IHisseRepository
    {
        List<Hisse> TumHisseleriGetir(HisselerFilterDto filter);
        void Kaydet(Hisse hisse);

        // Signal History
        void KaydetSignalHistory(Hisse hisse);
        List<SignalHistory> GetSignalHistory(string? sembol, int limit);
    }
}
