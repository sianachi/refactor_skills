using Catalog.Api.Common;
using Catalog.Api.Models;

namespace Catalog.Api.Validation;

public interface IProductValidator
{
    Result<bool> Validate(CreateProductRequest request);
}

public class ProductValidator : IProductValidator
{
    public Result<bool> Validate(CreateProductRequest request)
    {
        if (request == null)
        {
            return Result<bool>.Fail("body is required");
        }

        if (string.IsNullOrWhiteSpace(request.Name))
        {
            return Result<bool>.Fail("name is required");
        }

        if (string.IsNullOrWhiteSpace(request.Sku))
        {
            return Result<bool>.Fail("sku is required");
        }

        if (request.UnitPrice == null)
        {
            return Result<bool>.Fail("unit_price is required");
        }

        if (request.UnitPrice < 0)
        {
            return Result<bool>.Fail("unit_price must not be negative");
        }

        return Result<bool>.Ok(true);
    }
}
