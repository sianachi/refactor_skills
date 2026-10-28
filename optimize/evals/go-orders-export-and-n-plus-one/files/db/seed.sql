-- Small dev dataset.
INSERT INTO customers (name, email)
SELECT 'Customer ' || g, 'c' || g || '@example.com' FROM generate_series(1, 20) g;

INSERT INTO orders (customer_id, status, total_cents, note, created_at)
SELECT 1 + (g % 20), (ARRAY['open', 'paid', 'shipped', 'returned'])[1 + g % 4], 1000 + g * 7, 'note ' || g,
       timestamptz '2026-01-01 00:00:00+00' + g * interval '1 hour'
FROM generate_series(1, 200) g;

INSERT INTO order_items (order_id, sku, qty, price_cents)
SELECT 1 + (g % 200), 'SKU-' || (g % 30), 1 + g % 3, 250 + g % 500 FROM generate_series(1, 600) g;
