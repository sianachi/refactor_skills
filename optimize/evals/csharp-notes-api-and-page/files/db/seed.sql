-- Small dev dataset.
INSERT INTO users (name) SELECT 'User ' || g FROM generate_series(1, 10) g;
INSERT INTO notes (title, body, tag, author_id, created_at)
SELECT 'Note ' || g, 'Body of note ' || g, (ARRAY['work', 'home', 'ideas'])[1 + g % 3], 1 + g % 10,
       timestamp '2026-01-01' + g * interval '1 hour'
FROM generate_series(1, 100) g;
