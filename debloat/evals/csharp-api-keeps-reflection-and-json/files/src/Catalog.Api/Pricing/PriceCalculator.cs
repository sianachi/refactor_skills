using Catalog.Api.Models;

namespace Catalog.Api.Pricing;

public interface IPriceCalculator
{
    PriceQuoteDto Quote(Product product, int qty);
}

public class PriceCalculator : IPriceCalculator
{
    private readonly IEnumerable<IDiscountRule> _rules;

    public PriceCalculator(IEnumerable<IDiscountRule> rules)
    {
        _rules = rules;
    }

    public PriceQuoteDto Quote(Product product, int qty)
    {
        var subtotal = product.UnitPrice * qty;
        var rate = 0m;
        var applied = new List<string>();
        foreach (var rule in _rules)
        {
            var r = rule.RateFor(product, qty);
            if (r > 0)
            {
                rate = rate + r;
                applied.Add(rule.Name);
            }
        }

        if (rate > 0.6m)
        {
            rate = 0.6m;
        }

        var discount = Math.Round(subtotal * rate, 2, MidpointRounding.AwayFromZero);
        var quote = new PriceQuoteDto();
        quote.ProductId = product.Id;
        quote.Qty = qty;
        quote.Subtotal = subtotal;
        quote.Discount = discount;
        quote.Total = subtotal - discount;
        quote.AppliedRules = applied;
        return quote;
    }
}

public static class LegacyPriceFormatter
{
    public static string Format(decimal amount) => "$" + amount.ToString("0.00");
}
