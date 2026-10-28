-- 10k customers, 300k orders (customer 1 has ~3k, "returned" is 2%), 900k items. Deterministic.
INSERT INTO customers (name, email)
SELECT 'Customer ' || g, 'c' || g || '@example.com' FROM generate_series(1, 10000) g;

INSERT INTO orders (customer_id, status, total_cents, note, created_at)
SELECT CASE WHEN g % 97 = 0 THEN 1 ELSE 1 + (g::bigint * 7919) % 10000 END,
       CASE WHEN g % 50 = 7 THEN 'returned' ELSE (ARRAY['open', 'paid', 'shipped'])[1 + g % 3] END,
       (g::bigint * 104729) % 100000,
       repeat('n', 200 + g % 50),
       timestamptz '2025-01-01 00:00:00+00' + g * interval '1 minute'
FROM generate_series(1, 300000) g;

INSERT INTO order_items (order_id, sku, qty, price_cents)
SELECT 1 + (g * 31) % 300000, 'SKU-' || (g % 997), 1 + g % 5, 100 + (g * 13) % 9000
FROM generate_series(1, 900000) g;

ANALYZE;
