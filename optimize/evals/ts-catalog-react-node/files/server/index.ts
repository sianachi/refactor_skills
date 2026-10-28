import { createReadStream, existsSync, statSync } from "node:fs";
import { createServer } from "node:http";
import { extname, join, normalize } from "node:path";
import { ensureSchema } from "./db.ts";
import { categorySummary, exportJson, products } from "./routes.ts";

const dist = new URL("../web/dist/", import.meta.url).pathname;
const types: Record<string, string> = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml" };

const routes: Record<string, typeof products> = {
  "/api/products": products,
  "/api/categories/summary": categorySummary,
  "/api/products/export.json": exportJson,
};

await ensureSchema();

createServer(async (req, res) => {
  const url = new URL(req.url ?? "/", "http://localhost");
  const route = req.method === "GET" ? routes[url.pathname] : undefined;
  try {
    if (route) return await route(req, res);
    if (url.pathname.startsWith("/api/")) {
      res.writeHead(404, { "Content-Type": "application/json" }).end(JSON.stringify({ error: "not found" }));
      return;
    }
    let file = normalize(join(dist, url.pathname));
    if (!file.startsWith(dist) || !existsSync(file) || statSync(file).isDirectory()) file = join(dist, "index.html");
    res.writeHead(200, { "Content-Type": types[extname(file)] ?? "application/octet-stream" });
    createReadStream(file).pipe(res);
  } catch (err) {
    console.error(err);
    res.writeHead(500, { "Content-Type": "application/json" }).end(JSON.stringify({ error: "internal error" }));
  }
}).listen(Number(process.env.PORT ?? 3000), "127.0.0.1");
