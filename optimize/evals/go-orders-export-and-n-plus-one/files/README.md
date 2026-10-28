# orders

Order service for the warehouse team.

    DATABASE_URL=postgres://... PORT=8080 go run .

Migrations in `migrations/` run at startup, in file-name order. `db/seed.sql` loads a small dev dataset.

## Endpoints

- `GET /export/orders.csv[?status=paid]`: CSV export used by finance's monthly reconciliation script.
- `GET /customers/{id}/summary`: order and revenue totals for the support dashboard.
- `GET /orders[?status=...&customer_id=...]`: **public partner API**. Partner integrations (outside this repo) call it and
  expect the full JSON array; don't change the default response.
