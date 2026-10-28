using Catalog.Api.Common;
using Catalog.Api.Mapping;
using Catalog.Api.Pricing;
using Catalog.Api.Repositories;
using Catalog.Api.Services;
using Catalog.Api.Validation;

var builder = WebApplication.CreateBuilder(args);

builder.Services.Configure<CatalogOptions>(builder.Configuration.GetSection("Catalog"));
builder.Services.AddSingleton<IProductRepository, InMemoryProductRepository>();
builder.Services.AddScoped<IProductService, ProductService>();
builder.Services.AddScoped<IProductMapper, ProductMapper>();
builder.Services.AddScoped<IProductValidator, ProductValidator>();
builder.Services.AddScoped<IPriceCalculator, PriceCalculator>();
builder.Services.AddSingleton<IClock, SystemClock>();
builder.Services.AddDiscountRules();
builder.Services.AddControllers();

var app = builder.Build();

app.MapGet("/health", () => Results.Ok(new { status = "ok" }));
app.MapControllers();

app.Run();
