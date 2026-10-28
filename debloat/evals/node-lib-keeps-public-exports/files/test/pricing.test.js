import { test } from "node:test";
import assert from "node:assert/strict";
import { formatPrice, slugify } from "../src/index.js";
import { handle } from "../src/routes.js";

const ROWS = [{ name: "Blue Widget", price: 9.5 }];

test("formatPrice", () => {
  assert.equal(formatPrice(9.5), "$9.50");
});

test("slugify", () => {
  assert.equal(slugify("  Blue Widget! "), "blue-widget");
});

test("product route finds by slug", () => {
  const out = handle("GET /product", ROWS, "blue-widget");
  assert.equal(out.status, 200);
  assert.match(out.body, /Blue Widget\s+\$9\.50/);
});

test("prices route", () => {
  assert.match(handle("GET /prices", ROWS).body, /\$9\.50/);
});
