
using Microsoft.AspNetCore.SignalR;
using System.Threading.Tasks;

namespace BorsaAPI.Hubs
{
    public class BorsaHub : Hub
    {
        public override async Task OnConnectedAsync()
        {
            await base.OnConnectedAsync();
        }
    }
}
