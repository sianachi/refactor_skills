using Catalog.Api.Common;
using Catalog.Api.Mapping;
using Catalog.Api.Models;
using Catalog.Api.Pricing;
using Catalog.Api.Repositories;
using Catalog.Api.Validation;
using Microsoft.Extensions.Options;

namespace Catalog.Api.Services;

public interface IProductService
{
    Task<PagedResult<ProductDto>> ListAsync(int page, int pageSize);

    Task<Result<ProductDto>> GetAsync(int id);

    Task<Result<ProductDto>> CreateAsync(CreateProductRequest request);

    Task<Result<PriceQuoteDto>> QuoteAsync(int id, int qty);
}

public class ProductService : IProductService
{
    private readonly IProductRepository _repository;
    private readonly IProductMapper _mapper;
    private readonly IProductValidator _validator;
    private readonly IPriceCalculator _calculator;
    private readonly IClock _clock;
    private readonly CatalogOptions _options;

    public ProductService(
        IProductRepository repository,
        IProductMapper mapper,
        IProductValidator validator,
        IPriceCalculator calculator,
        IClock clock,
        IOptions<CatalogOptions> options)
    {
        _repository = repository;
        _mapper = mapper;
        _validator = validator;
        _calculator = calculator;
        _clock = clock;
        _options = options.Value;
    }

    public async Task<PagedResult<ProductDto>> ListAsync(int page, int pageSize)
    {
        if (page < 1)
        {
            page = Constants.DefaultPage;
        }

        if (pageSize < 1)
        {
            pageSize = Constants.DefaultPageSize;
        }

        if (pageSize > _options.MaxPageSize)
        {
            pageSize = _options.MaxPageSize;
        }

        var all = await _repository.GetAllAsync();
        var items = all.Skip((page - 1) * pageSize).Take(pageSize).Select(p => _mapper.ToDto(p)).ToList();
        var result = new PagedResult<ProductDto>();
        result.Items = items;
        result.Page = page;
        result.PageSize = pageSize;
        result.Total = all.Count;
        return result;
    }

    public async Task<Result<ProductDto>> GetAsync(int id)
    {
        var product = await _repository.GetByIdAsync(id);
        if (product == null)
        {
            return Result<ProductDto>.Fail("not found");
        }

        return Result<ProductDto>.Ok(_mapper.ToDto(product));
    }

    public async Task<Result<ProductDto>> CreateAsync(CreateProductRequest request)
    {
        var validation = _validator.Validate(request);
        if (!validation.Success)
        {
            return Result<ProductDto>.Fail(validation.Error!);
        }

        var product = _mapper.FromRequest(request);
        product.CreatedAt = _clock.UtcNow;
        var saved = await _repository.AddAsync(product);
        return Result<ProductDto>.Ok(_mapper.ToDto(saved));
    }

    public async Task<Result<PriceQuoteDto>> QuoteAsync(int id, int qty)
    {
        if (qty < 1)
        {
            return Result<PriceQuoteDto>.Fail("qty must be at least 1");
        }

        var exists = await _repository.ExistsAsync(id);
        if (!exists)
        {
            return Result<PriceQuoteDto>.Fail("not found");
        }

        var product = await _repository.GetByIdAsync(id);
        return Result<PriceQuoteDto>.Ok(_calculator.Quote(product!, qty));
    }
}
