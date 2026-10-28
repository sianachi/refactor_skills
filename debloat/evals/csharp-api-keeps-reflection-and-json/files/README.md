# Catalog API

HTTP API used by the storefront and the mobile app. The routes and JSON bodies are the contract.

    dotnet run --project src/Catalog.Api --urls http://127.0.0.1:5080

- `GET /health`
- `GET /products?page=1&pageSize=10` (page size is capped by `Catalog:MaxPageSize`)
- `GET /products/{id}`
- `POST /products` with `{ "name": "...", "sku": "...", "unit_price": 1.5 }`
- `GET /products/{id}/price?qty=1`
