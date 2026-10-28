-- 2k users, 200k notes with ~600-char bodies, tricky titles, tied timestamps. Deterministic.
INSERT INTO users (name) SELECT 'User ' || g FROM generate_series(1, 2000) g;

INSERT INTO notes (title, body, tag, author_id, created_at)
SELECT CASE WHEN g % 997 = 0 THEN 'Report 50% done ' || g
            ELSE (ARRAY['Café plan', 'cafe PLAN', 'snake_case notes', 'Über ideas', 'ÉCOLE trip', 'Weekly sync',
                        'Budget Q3', 'retro notes', 'Plan B', 'grocery list', 'Reading list', 'Ideas: 100%'])[1 + g % 12]
                 || ' ' || g END,
       repeat('Lorem ipsum dolor sit amet ' || g || '. ', 20),
       (ARRAY['work', 'home', 'ideas', 'travel', 'finance', 'health', 'books', 'misc'])[1 + (g / 5) % 8],
       1 + (g::bigint * 7919) % 2000,
       timestamptz '2025-01-01 00:00:00+00' + (g / 3) * interval '1 minute'
FROM generate_series(1, 200000) g;

ANALYZE;
