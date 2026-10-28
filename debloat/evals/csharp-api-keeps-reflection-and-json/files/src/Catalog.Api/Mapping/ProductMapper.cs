using Catalog.Api.Models;

namespace Catalog.Api.Mapping;

public interface IProductMapper
{
    ProductDto ToDto(Product product);

    Product FromRequest(CreateProductRequest request);
}

public class ProductMapper : IProductMapper
{
    public ProductDto ToDto(Product product)
    {
        var dto = new ProductDto();
        dto.Id = product.Id;
        dto.Name = product.Name;
        dto.Sku = product.Sku;
        dto.UnitPrice = product.UnitPrice;
        return dto;
    }

    public Product FromRequest(CreateProductRequest request)
    {
        var product = new Product();
        product.Name = request.Name!.Trim();
        product.Sku = request.Sku!.Trim().ToUpperInvariant();
        product.UnitPrice = request.UnitPrice!.Value;
        return product;
    }
}
