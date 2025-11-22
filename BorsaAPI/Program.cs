using BorsaAPI.Models;
using BorsaAPI.Services;
using Microsoft.OpenApi.Models; // Bu kütüphane şart!

var builder = WebApplication.CreateBuilder(args);

// --- 1. SERVİSLER ---
builder.Services.AddCors(options =>
{
    options.AddPolicy("HerkesGelsinPolitikasi", policy =>
    {
        policy.AllowAnyOrigin()  // Hangi siteden gelirse gelsin (localhost, google.com vb.)
              .AllowAnyMethod()  // GET, POST, PUT, DELETE hepsi serbest
              .AllowAnyHeader(); // Tüm başlıklara izin ver
    });
});
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();

// DÜZELTME 1: Swagger'a "v1" adında bir döküman oluştur diyoruz.
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new OpenApiInfo { Title = "BorsaAPI", Version = "v1" });
});

builder.Services.AddScoped<IHisseRepository, HisseRepository>(); // Service sınıfını kullanıyoruz

var app = builder.Build();

// --- 2. UYGULAMA AYARLARI ---
app.UseCors("HerkesGelsinPolitikasi");

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI(c => 
    {
        c.SwaggerEndpoint("/swagger/v1/swagger.json", "BorsaAPI v1");
    });
}

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    
    // DÜZELTME 2: Yukarıda oluşturduğumuz "v1" dökümanını bu adreste sun diyoruz.
    app.UseSwaggerUI(c => 
    {
        c.SwaggerEndpoint("/swagger/v1/swagger.json", "BorsaAPI v1");
    });
}

app.UseHttpsRedirection();
app.UseAuthorization();
app.UseCors("HerkesGelsinPolitikasi");
app.MapControllers();

app.Run();