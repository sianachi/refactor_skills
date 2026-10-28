CREATE TABLE customers (
    id    serial PRIMARY KEY,
    name  text NOT NULL,
    email text NOT NULL
);

CREATE TABLE orders (
    id          bigserial PRIMARY KEY,
    customer_id int NOT NULL REFERENCES customers (id),
    status      text NOT NULL,
    total_cents int NOT NULL,
    note        text NOT NULL DEFAULT '',
    created_at  timestamptz NOT NULL
);

CREATE TABLE order_items (
    id          bigserial PRIMARY KEY,
    order_id    bigint NOT NULL REFERENCES orders (id),
    sku         text NOT NULL,
    qty         int NOT NULL,
    price_cents int NOT NULL
);
