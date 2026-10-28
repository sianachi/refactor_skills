// Hidden contract tests: the package entry and the HTTP server only.
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import * as pkg from "../src/index.js";

test("package exports", () => {
  assert.deepEqual(Object.keys(pkg).sort(), ["formatPrice", "slugify"]);
  assert.equal(pkg.formatPrice(1234.5), "$1,234.50");
  assert.equal(pkg.formatPrice(5, "EUR"), "€5.00");
  assert.equal(pkg.formatPrice(0), "$0.00");
  assert.equal(pkg.slugify("  Hello,  World!! "), "hello-world");
  assert.equal(pkg.slugify("---"), "");
  assert.equal(pkg.slugify("Ünïcode Name 2"), "n-code-name-2");
});

test("server routes", async () => {
  const port = 40000 + Math.floor(Math.random() * 20000);
  const srv = spawn(process.execPath, ["src/server.js"], { env: { ...process.env, PORT: String(port) } });
  try {
    let ok = false;
    for (let i = 0; i < 50 && !ok; i++) {
      await new Promise((r) => setTimeout(r, 100));
      ok = await fetch(`http://127.0.0.1:${port}/health`).then(() => true, () => false);
    }
    const get = async (p) => { const r = await fetch(`http://127.0.0.1:${port}${p}`); return [r.status, await r.text()]; };
    assert.deepEqual(await get("/health"), [200, "ok"]);
    assert.deepEqual(await get("/prices"), [200, "Blue Widget  $9.50\nRed Gadget   $12.00"]);
    assert.deepEqual(await get("/product?name=red-gadget"), [200, "Red Gadget   $12.00"]);
    assert.deepEqual(await get("/product?name=nope"), [404, "not found"]);
    assert.deepEqual(await get("/product"), [404, "not found"]);
    assert.deepEqual(await get("/missing"), [404, "not found"]);
    const r = await fetch(`http://127.0.0.1:${port}/health`, { method: "POST" });
    assert.deepEqual([r.status, await r.text()], [404, "not found"]);
  } finally {
    srv.kill();
  }
});
