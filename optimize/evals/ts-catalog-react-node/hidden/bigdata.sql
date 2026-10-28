-- 100k products with ~1KB descriptions, mixed-case and accented names, tied prices. Deterministic.
INSERT INTO products (name, category, price, description)
SELECT CASE WHEN g % 1999 = 0 THEN 'Limited Édition ' || g
            ELSE (ARRAY['apple crate', 'Apple pie tin', 'éclair mold', 'Eclair box', 'zebra mug', 'Zebra Mug XL',
                        'banana hook', 'Bänd saw', '100% cotton tee', 'snake_plant pot', 'Garden hose', 'kitchen timer'])[1 + g % 12]
                 || ' ' || g END,
       (ARRAY['tools', 'garden', 'kitchen', 'apparel', 'decor', 'outdoor', 'storage', 'pets', 'bath', 'office'])[1 + (g / 7) % 10],
       ((g::bigint * 7919) % 50000) / 100.0,
       repeat('Durable and well made. Item ' || g || '. ', 30)
FROM generate_series(1, 100000) g;

ANALYZE;
