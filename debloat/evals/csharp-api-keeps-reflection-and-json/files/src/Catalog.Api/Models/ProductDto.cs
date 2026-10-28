using System.Text.Json.Serialization;

namespace Catalog.Api.Models;

public class ProductDto
{
    public int Id { get; set; }

    public string Name { get; set; } = "";

    public string Sku { get; set; } = "";

    [JsonPropertyName("unit_price")]
    public decimal UnitPrice { get; set; }
}

public class CreateProductRequest
{
    public string? Name { get; set; }

    public string? Sku { get; set; }

    [JsonPropertyName("unit_price")]
    public decimal? UnitPrice { get; set; }
}

public class PriceQuoteDto
{
    public int ProductId { get; set; }

    public int Qty { get; set; }

    public decimal Subtotal { get; set; }

    public decimal Discount { get; set; }

    public decimal Total { get; set; }

    public List<string> AppliedRules { get; set; } = new();
}

public class PagedResult<T>
{
    public List<T> Items { get; set; } = new();

    public int Page { get; set; }

    public int PageSize { get; set; }

    public int Total { get; set; }
}
