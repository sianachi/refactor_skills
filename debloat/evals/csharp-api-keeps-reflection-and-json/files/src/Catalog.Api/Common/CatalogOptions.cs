namespace Catalog.Api.Common;

public class CatalogOptions
{
    public int MaxPageSize { get; set; } = 50;

    public string Currency { get; set; } = "USD";
}
