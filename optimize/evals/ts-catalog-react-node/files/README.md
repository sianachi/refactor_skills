# Catalog

Product catalog: a Node API (`server/`, plain `node:http` + `pg`) and the React app in `web/` that is its only
interactive client.

    npm install
    npm run build          # builds web/ into web/dist
    DATABASE_URL=postgres://... PORT=3000 npm start

`server/schema.sql` is applied at startup if the table is missing. `db/seed.sql` loads a small dev dataset.

`GET /api/products/export.json` feeds the marketing team's nightly product feed job (outside this repo), which
parses the JSON array; keep its format unchanged.
