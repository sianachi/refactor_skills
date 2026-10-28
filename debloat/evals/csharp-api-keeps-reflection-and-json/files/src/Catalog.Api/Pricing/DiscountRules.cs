using Catalog.Api.Models;

namespace Catalog.Api.Pricing;

public interface IDiscountRule
{
    string Name { get; }

    decimal RateFor(Product product, int qty);
}

public class BulkDiscountRule : IDiscountRule
{
    public string Name => "bulk";

    public decimal RateFor(Product product, int qty) => qty >= 10 ? 0.10m : 0m;
}

public class ClearanceDiscountRule : IDiscountRule
{
    public string Name => "clearance";

    public decimal RateFor(Product product, int qty) => product.Sku.StartsWith("CLR-") ? 0.50m : 0m;
}

public static class DiscountRuleRegistration
{
    // Every IDiscountRule in this assembly is picked up, so new rules need no wiring.
    public static IServiceCollection AddDiscountRules(this IServiceCollection services)
    {
        var ruleTypes = typeof(IDiscountRule).Assembly
            .GetTypes()
            .Where(t => typeof(IDiscountRule).IsAssignableFrom(t) && t.IsClass && !t.IsAbstract)
            .OrderBy(t => t.Name);
        foreach (var type in ruleTypes)
        {
            services.AddSingleton(typeof(IDiscountRule), type);
        }

        return services;
    }
}
