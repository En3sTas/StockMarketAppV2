
using BorsaAPI.Models;
using BorsaAPI.Services;
using BorsaAPI.Hubs;
using Microsoft.OpenApi.Models;

var builder = WebApplication.CreateBuilder(args);

// 1. Services Configuration
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
builder.Services.AddScoped<IHisseRepository, HisseRepository>();
builder.Services.AddScoped<IHisseService, HisseService>();
builder.Services.AddHostedService<RabbitMQConsumer>();

var app = builder.Build();

// 2. HTTP Request Pipeline
app.UseCors("AllowAll");

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI(c =>
    {
        c.SwaggerEndpoint("/swagger/v1/swagger.json", "BorsaAPI v1");
    });
}

app.UseHttpsRedirection();
app.UseAuthorization();

// Static Files (for Frontend hosting)
app.UseDefaultFiles(); 
app.UseStaticFiles();  

app.MapControllers();

// SignalR Endpoints
app.MapHub<BorsaHub>("/hubs/borsa");

app.Run();