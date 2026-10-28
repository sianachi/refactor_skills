export type Product = { id: number; name: string; category: string; price: string; description: string };
export type CategorySummary = { category: string; count: number; avgPrice: number };

export async function fetchProducts(): Promise<Product[]> {
  const res = await fetch("/api/products");
  return res.json();
}

export async function fetchCategories(): Promise<CategorySummary[]> {
  const res = await fetch("/api/categories/summary");
  return res.json();
}
