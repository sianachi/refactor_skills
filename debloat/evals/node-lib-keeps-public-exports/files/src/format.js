import { renderRow } from "./table.js";

export function formatPrice(amount, currency = "USD") {
  return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(amount);
}

// Formats a price. Calls formatPrice.
export function format(amount) {
  return formatPrice(amount);
}

export function priceTable(rows) {
  return rows.map((r) => renderRow(r)).join("\n");
}
