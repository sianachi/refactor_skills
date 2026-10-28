// In-memory cache, replaced by the CDN in 2023.
const cache = new Map();

export function cached(key, fn) {
  if (!cache.has(key)) cache.set(key, fn());
  return cache.get(key);
}
