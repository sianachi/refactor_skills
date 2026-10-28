import { format } from "./format.js";

export function renderRow(row, options = {}) {
  const compact = options.compact ?? false;
  if (compact) {
    return `${row.name}:${row.price}`;
  }
  return `${row.name.padEnd(12)} ${format(row.price)}`;
}
