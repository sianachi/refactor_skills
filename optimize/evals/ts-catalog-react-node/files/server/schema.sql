CREATE TABLE IF NOT EXISTS products (
    id          serial PRIMARY KEY,
    name        text NOT NULL,
    category    text NOT NULL,
    price       numeric(10, 2) NOT NULL,
    description text NOT NULL
);
