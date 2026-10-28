import type { IncomingMessage, ServerResponse } from "node:http";
import { allProducts } from "./db.ts";

function sendJson(res: ServerResponse, status: number, body: unknown): void {
  res.writeHead(status, { "Content-Type": "application/json" });
  res.end(JSON.stringify(body));
}

export async function products(_req: IncomingMessage, res: ServerResponse): Promise<void> {
  sendJson(res, 200, await allProducts());
}

export async function categorySummary(_req: IncomingMessage, res: ServerResponse): Promise<void> {
  const rows = await allProducts();
  const byCategory = new Map<string, { count: number; total: number }>();
  for (const p of rows) {
    const entry = byCategory.get(p.category) ?? { count: 0, total: 0 };
    entry.count++;
    entry.total += Number(p.price);
    byCategory.set(p.category, entry);
  }
  const summary = [...byCategory.entries()]
    .map(([category, e]) => ({ category, count: e.count, avgPrice: Math.round((e.total / e.count) * 100) / 100 }))
    .sort((a, b) => (a.category < b.category ? -1 : a.category > b.category ? 1 : 0));
  sendJson(res, 200, summary);
}

export async function exportJson(_req: IncomingMessage, res: ServerResponse): Promise<void> {
  const rows = await allProducts();
  sendJson(res, 200, rows);
}
