
using BorsaAPI.Models;
using BorsaAPI.Services;
using BorsaAPI.Hubs;
using Microsoft.OpenApi.Models;

var builder = WebApplication.CreateBuilder(args);

// ── Services ──────────────────────────────────────────────────────────────────
builder.Services.AddSignalR();

builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", policy =>
    {
        policy.SetIsOriginAllowed(origin => true)
              .AllowAnyMethod()
              .AllowAnyHeader()
              .AllowCredentials();
    });
});

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();

builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new OpenApiInfo { Title = "BorsaAPI", Version = "v1" });
});

// Dependency Injection
builder.Services.AddScoped<IStockRepository, StockRepository>();
builder.Services.AddScoped<IStockService, StockService>();
builder.Services.AddHostedService<RabbitMQConsumer>();

var app = builder.Build();

// ── HTTP Pipeline ─────────────────────────────────────────────────────────────
app.UseCors("AllowAll");

// Swagger: available in all environments (Docker runs HTTP-only)
app.UseSwagger();
app.UseSwaggerUI(c =>
{
    c.SwaggerEndpoint("/swagger/v1/swagger.json", "BorsaAPI v1");
});

// HTTPS termination is handled by the reverse proxy / load balancer upstream.
// Do NOT use UseHttpsRedirection() in a Docker HTTP-only container.

app.UseAuthorization();

// Static Files (Frontend hosting — wwwroot)
app.UseDefaultFiles();
app.UseStaticFiles();

app.MapControllers();

// SignalR Hub
app.MapHub<BorsaHub>("/hubs/borsa");

app.Run();