namespace Catalog.Api.Common;

// Planned: cache product lookups once the catalog moves to a database.
public interface ICacheProvider
{
    T? Get<T>(string key);

    void Set<T>(string key, T value, TimeSpan ttl);
}
