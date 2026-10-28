namespace Catalog.Api.Models;

public class Product
{
    public int Id { get; set; }

    public string Name { get; set; } = "";

    public string Sku { get; set; } = "";

    public decimal UnitPrice { get; set; }

    public DateTime CreatedAt { get; set; }
}
