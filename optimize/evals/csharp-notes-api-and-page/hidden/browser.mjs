// Drives the notes page like a user and prints what it shows, plus API bytes and requests per step.
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

async function settle() {
  let last = "", stableSince = Date.now();
  const deadline = Date.now() + 120_000;
  while (Date.now() < deadline) {
    const now = await page.evaluate(() => document.getElementById("count").textContent + "|" + document.querySelectorAll("li.note").length);
    if (now !== last) { last = now; stableSince = Date.now(); }
    else if (Date.now() - stableSince > 1500 && !now.startsWith("Loading")) return;
    await page.waitForTimeout(200);
  }
}

async function snapshot(label, walkAll = false) {
  await settle();
  if (walkAll) {
    for (let i = 0; i < 400; i++) {
      const before = await page.locator("li.note").count();
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      const more = page.getByRole("button", { name: /load more|show more/i });
      if (await more.count()) await more.first().click().catch(() => {});
      await page.waitForTimeout(300);
      await settle();
      if ((await page.locator("li.note").count()) === before) break;
    }
  }
  const s = await page.evaluate((all) => {
    const items = [...document.querySelectorAll("li.note")];
    return {
      count: document.getElementById("count").textContent,
      rendered: items.length,
      items: (all ? items : items.slice(0, 30)).map((li) => [li.dataset.id, li.querySelector("h3")?.textContent, li.querySelector("p")?.textContent, li.querySelector("small")?.textContent].join("~")),
    };
  }, walkAll);
  await Promise.all(pending);
  console.log(JSON.stringify({ step: label, ...s, apiBytes, apiRequests }));
  apiBytes = 0; apiRequests = 0; pending = [];
}

async function type(text) {
  await page.fill("#search", "");
  await page.locator("#search").pressSequentially(text, { delay: 60 });
}

await page.goto(base + "/", { timeout: 180_000 });
await snapshot("initial");
for (const q of ["café", "Über", "ecole", "snake_", "50%", "plan", "zzzz-none"]) {
  await type(q);
  await snapshot("search:" + q, q === "50%");
}
await type("plan");
await page.selectOption("#tag", "ideas");
await snapshot("tag:ideas+plan");
await page.fill("#search", "");
await page.locator("#search").dispatchEvent("input");
await snapshot("tag:ideas");
await browser.close();
