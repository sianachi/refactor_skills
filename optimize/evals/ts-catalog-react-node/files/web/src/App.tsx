import { useEffect, useState } from "react";
import { fetchCategories, fetchProducts, type CategorySummary, type Product } from "./api.ts";

type Sort = "name" | "price-asc" | "price-desc";

export function App() {
  const [products, setProducts] = useState<Product[] | null>(null);
  const [categories, setCategories] = useState<CategorySummary[]>([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [sort, setSort] = useState<Sort>("name");

  useEffect(() => {
    fetchProducts().then(setProducts);
    fetchCategories().then(setCategories);
  }, []);

  if (!products) return <p className="status">Loading…</p>;

  const q = search.toLowerCase();
  const shown = products
    .filter((p) => p.name.toLowerCase().includes(q) && (!category || p.category === category))
    .sort((a, b) =>
      sort === "name" ? a.name.localeCompare(b.name) : sort === "price-asc" ? Number(a.price) - Number(b.price) : Number(b.price) - Number(a.price),
    );

  return (
    <main>
      <h1>Catalog</h1>
      <div className="toolbar">
        <input aria-label="Search products" placeholder="Search products" value={search} onChange={(e) => setSearch(e.target.value)} />
        <select aria-label="Category" value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="">All categories</option>
          {categories.map((c) => (
            <option key={c.category} value={c.category}>
              {c.category} ({c.count}, avg ${c.avgPrice.toFixed(2)})
            </option>
          ))}
        </select>
        <select aria-label="Sort" value={sort} onChange={(e) => setSort(e.target.value as Sort)}>
          <option value="name">Name</option>
          <option value="price-asc">Price: low to high</option>
          <option value="price-desc">Price: high to low</option>
        </select>
      </div>
      <p className="status">{shown.length} products</p>
      <ul className="products">
        {shown.map((p) => (
          <li key={p.id} className="product" data-id={p.id}>
            <span className="name">{p.name}</span>
            <span className="category">{p.category}</span>
            <span className="price">${Number(p.price).toFixed(2)}</span>
          </li>
        ))}
      </ul>
    </main>
  );
}
