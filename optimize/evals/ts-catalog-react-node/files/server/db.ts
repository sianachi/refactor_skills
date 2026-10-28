import { readFileSync } from "node:fs";
import pg from "pg";

export const pool = new pg.Pool({ connectionString: process.env.DATABASE_URL });

export async function ensureSchema(): Promise<void> {
  await pool.query(readFileSync(new URL("./schema.sql", import.meta.url), "utf8"));
}

export type Product = { id: number; name: string; category: string; price: string; description: string };

export async function allProducts(): Promise<Product[]> {
  const { rows } = await pool.query<Product>("SELECT * FROM products ORDER BY id");
  return rows;
}
