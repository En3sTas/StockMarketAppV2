using Microsoft.AspNetCore.SignalR;
using System.Threading.Tasks;

namespace BorsaAPI.Hubs
{
    public class BorsaHub : Hub
    {
        // Client'lar bağlandığında tetiklenir
        public override async Task OnConnectedAsync()
        {
            await base.OnConnectedAsync();
        }

        // Python'dan gelen veriyi Frontend'e yayınlayan metod
        // Aslında Python controller'a POST atacak, Controller da bu HubContext'i kullanıp yayınlayacak.
        // Ama yine de client'ların doğrudan çağırabileceği metodlar buraya yazılabilir.
    }
}
