using BorsaAPI.Models;
using BorsaAPI.Services;
using Microsoft.OpenApi.Models;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddCors(options =>
{
    options.AddPolicy("HerkesGelsinPolitikasi", policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
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
app.MapControllers();

app.Run();