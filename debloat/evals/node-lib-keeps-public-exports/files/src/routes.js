import { priceTable } from "./format.js";

function toSlug(text) {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

const handlers = {
  healthHandler: () => ({ status: 200, body: "ok" }),
  pricesHandler: (rows) => ({ status: 200, body: priceTable(rows) }),
  productHandler: (rows, name) => {
    const row = rows.find((r) => toSlug(r.name) === name);
    return row ? { status: 200, body: priceTable([row]) } : { status: 404, body: "not found" };
  },
};

// Route table is also read by deploy/healthcheck.yaml.
export const routes = {
  "GET /health": "healthHandler",
  "GET /prices": "pricesHandler",
  "GET /product": "productHandler",
};

export function handle(route, ...args) {
  const name = routes[route];
  if (!name) return { status: 404, body: "not found" };
  return handlers[name](...args);
}
