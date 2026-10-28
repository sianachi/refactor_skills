-- Small dev dataset.
INSERT INTO products (name, category, price, description)
SELECT 'Product ' || g, (ARRAY['tools', 'garden', 'kitchen'])[1 + g % 3], (g * 1.25)::numeric(10, 2), 'Description ' || g
FROM generate_series(1, 60) g;
