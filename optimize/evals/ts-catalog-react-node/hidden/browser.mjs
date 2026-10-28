// Drives the catalog page like a user and prints what it shows, plus API bytes and requests per step.
// Usage: node browser.mjs <baseUrl>
const { chromium } = await import(process.env.PLAYWRIGHT_CORE ?? "playwright-core");

const base = process.argv[2];
const browser = await chromium.launch();
const page = await browser.newPage();
let apiBytes = 0, apiRequests = 0, pending = [];
page.on("requestfinished", (req) => {
  if (!req.url().includes("/api/")) return;
  apiRequests++;
  pending.push(req.sizes().then((s) => { apiBytes += s.responseBodySize; }, () => {}));
});
const search = page.getByLabel("Search products");
const category = page.getByLabel("Category");
const sort = page.getByLabel("Sort");

async function settle() {
  let last = "", stableSince = Date.now();
  const deadline = Date.now() + 120_000;
  while (Date.now() < deadline) {
    const now = await page.evaluate(() => (document.querySelector("p.status")?.textContent ?? "") + "|" + document.querySelectorAll("li.product").length + "|" + (document.querySelector("li.product")?.dataset.id ?? ""));
    if (now !== last) { last = now; stableSince = Date.now(); }
    else if (Date.now() - stableSince > 1500 && !now.startsWith("Loading")) return;
    await page.waitForTimeout(200);
  }
}

async function snapshot(label, walkAll = false) {
  await settle();
  if (walkAll) {
    for (let i = 0; i < 400; i++) {
      const before = await page.locator("li.product").count();
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      const more = page.getByRole("button", { name: /load more|show more/i });
      if (await more.count()) await more.first().click().catch(() => {});
      await page.waitForTimeout(300);
      await settle();
      if ((await page.locator("li.product").count()) === before) break;
    }
  }
  const s = await page.evaluate((all) => {
    const items = [...document.querySelectorAll("li.product")];
    return {
      count: document.querySelector("p.status")?.textContent,
      options: [...document.querySelectorAll('select[aria-label="Category"] option')].map((o) => o.textContent),
      rendered: items.length,
      items: (all ? items : items.slice(0, 30)).map((li) => [li.dataset.id, li.querySelector(".name")?.textContent, li.querySelector(".category")?.textContent, li.querySelector(".price")?.textContent].join("~")),
    };
  }, walkAll);
  await Promise.all(pending);
  console.log(JSON.stringify({ step: label, ...s, apiBytes, apiRequests }));
  apiBytes = 0; apiRequests = 0; pending = [];
}

async function type(text) {
  await search.fill("");
  await search.pressSequentially(text, { delay: 60 });
}

await page.goto(base + "/", { timeout: 180_000 });
await snapshot("initial");
for (const q of ["apple", "éclair", "eclair", "ZEBRA", "100%", "snake_", "bänd"]) {
  await type(q);
  await snapshot("search:" + q);
}
await type("édition");
await snapshot("search:édition (all pages)", true);
await type("");
await search.dispatchEvent("input");
await category.selectOption("garden");
await snapshot("category:garden");
await sort.selectOption("price-asc");
await snapshot("garden price-asc");
await sort.selectOption("price-desc");
await snapshot("garden price-desc");
await category.selectOption("");
await type("zebra");
await sort.selectOption("name");
await snapshot("zebra by name");
await browser.close();
