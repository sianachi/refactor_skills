using Catalog.Api.Models;

namespace Catalog.Api.Repositories;

public interface IProductRepository
{
    Task<Product?> GetByIdAsync(int id);

    Task<List<Product>> GetAllAsync();

    Task<Product> AddAsync(Product product);

    Task<bool> ExistsAsync(int id);
}

public class InMemoryProductRepository : IProductRepository
{
    private readonly List<Product> _products = new()
    {
        new Product { Id = 1, Name = "Blue Widget", Sku = "BW-1", UnitPrice = 9.50m },
        new Product { Id = 2, Name = "Red Gadget", Sku = "RG-2", UnitPrice = 12.00m },
        new Product { Id = 3, Name = "Old Lamp", Sku = "CLR-3", UnitPrice = 40.00m },
    };

    private readonly object _lock = new();

    public Task<Product?> GetByIdAsync(int id)
    {
        lock (_lock)
        {
            return Task.FromResult(_products.FirstOrDefault(p => p.Id == id));
        }
    }

    public Task<List<Product>> GetAllAsync()
    {
        lock (_lock)
        {
            return Task.FromResult(_products.OrderBy(p => p.Id).ToList());
        }
    }

    public Task<Product> AddAsync(Product product)
    {
        lock (_lock)
        {
            product.Id = _products.Max(p => p.Id) + 1;
            _products.Add(product);
            return Task.FromResult(product);
        }
    }

    public Task<bool> ExistsAsync(int id)
    {
        lock (_lock)
        {
            return Task.FromResult(_products.Any(p => p.Id == id));
        }
    }
}
