using BorsaAPI.Models;
using BorsaAPI.Services;
using BorsaAPI.Hubs; // Import Namespace
using Microsoft.OpenApi.Models;

var builder = WebApplication.CreateBuilder(args);

// --- SIGNALR SERVICE ---
builder.Services.AddSignalR();

builder.Services.AddCors(options =>
{
    options.AddPolicy("HerkesGelsinPolitikasi", policy =>
    {
        policy.SetIsOriginAllowed(origin => true) // Allow any origin
              .AllowAnyMethod()
              .AllowAnyHeader()
              .AllowCredentials(); // SignalR needs this for connection stability
    });
});
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();


builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new OpenApiInfo { Title = "BorsaAPI", Version = "v1" });
});

builder.Services.AddScoped<IHisseRepository, HisseRepository>();

var app = builder.Build();

app.UseCors("HerkesGelsinPolitikasi");

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
app.UseCors("HerkesGelsinPolitikasi");

// --- STATIC FILES (Frontend Hosting) ---
app.UseDefaultFiles(); // index.html automatic lookup
app.UseStaticFiles();  // wwwroot access

app.MapControllers();

// --- SIGNALR ENDPOINT ---
app.MapHub<BorsaHub>("/hubs/borsa");

app.Run();