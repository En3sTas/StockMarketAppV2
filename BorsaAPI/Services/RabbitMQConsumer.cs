
using BorsaAPI.Hubs;
using BorsaAPI.Models;
using Microsoft.AspNetCore.SignalR;
using RabbitMQ.Client;
using RabbitMQ.Client.Events;
using System.Text;
using System.Text.Json;

namespace BorsaAPI.Services
{
    public class RabbitMQConsumer : BackgroundService
    {
        private readonly IServiceProvider _serviceProvider;
        private readonly ILogger<RabbitMQConsumer> _logger;
        private readonly IConfiguration _configuration;
        private IConnection _connection;
        private IModel _channel;
        private const string QueueName = "stock_updates";

        public RabbitMQConsumer(IServiceProvider serviceProvider, ILogger<RabbitMQConsumer> logger, IConfiguration configuration)
        {
            _serviceProvider = serviceProvider;
            _logger = logger;
            _configuration = configuration;
            InitializeRabbitMQ();
        }

        private void InitializeRabbitMQ()
        {
            var factory = new ConnectionFactory()
            {
                HostName = _configuration["RabbitMQ:HostName"] ?? "localhost",
                Port = int.Parse(_configuration["RabbitMQ:Port"] ?? "5672"),
                UserName = _configuration["RabbitMQ:UserName"] ?? "guest",
                Password = _configuration["RabbitMQ:Password"] ?? "guest"
            };
            
            try
            {
                _connection = factory.CreateConnection();
                _channel = _connection.CreateModel();
                _channel.QueueDeclare(queue: QueueName,
                                     durable: false,
                                     exclusive: false,
                                     autoDelete: false,
                                     arguments: null);
                _logger.LogInformation("Connected to RabbitMQ.");
            }
            catch (Exception ex)
            {
                _logger.LogError($"Could not connect to RabbitMQ: {ex.Message}");
            }
        }

        protected override Task ExecuteAsync(CancellationToken stoppingToken)
        {
             if (_channel == null) return Task.CompletedTask;

            var consumer = new EventingBasicConsumer(_channel);
            consumer.Received += async (model, ea) =>
            {
                var body = ea.Body.ToArray();
                var message = Encoding.UTF8.GetString(body);
                
                try 
                {
                    var hisse = JsonSerializer.Deserialize<Hisse>(message);
                    if (hisse != null)
                    {
                        using (var scope = _serviceProvider.CreateScope())
                        {
                            var repository = scope.ServiceProvider.GetRequiredService<IHisseRepository>();
                            var hubContext = scope.ServiceProvider.GetRequiredService<IHubContext<BorsaHub>>();

                            // 1. Save to DB (upsert)
                            repository.Kaydet(hisse);

                            // 2. Save to Signal History (only actionable signals)
                            var trackSignals = new[] { "BUY", "STRONG_BUY", "WATCH" };
                            if (trackSignals.Contains(hisse.Signal))
                            {
                                repository.KaydetSignalHistory(hisse);
                            }

                            // 3. Real-time Broadcast
                            await hubContext.Clients.All.SendAsync("ReceiveStockUpdate", hisse);
                        }
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogError($"Error processing message: {ex.Message}");
                }
            };

            _channel.BasicConsume(queue: QueueName,
                                 autoAck: true,
                                 consumer: consumer);

            return Task.CompletedTask;
        }

        public override void Dispose()
        {
            _channel?.Close();
            _connection?.Close();
            base.Dispose();
        }
    }
}
