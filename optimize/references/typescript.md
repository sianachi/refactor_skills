# TypeScript, JavaScript, React and Node

Read this when the scope is a JS/TS frontend or a Node backend. It adds to SKILL.md; read `sql-postgres.md` too when the backend uses Postgres.

## Measuring

- **Node memory**: `process.memoryUsage().rss` sampled during the request, or the peak from `/usr/bin/time -l node ...` (macOS) or `/usr/bin/time -v` (Linux).
- **Frontend**: drive the page with Playwright (or the project's e2e tool). Count rendered rows with `page.locator(...).count()`, and requests and bytes with `page.on('response')`. Also time how long the list takes to appear. Use the production build (`vite build && vite preview`, `next build && next start`), not the dev server.
- **Bundle size**: the build's own size report. Use `rollup-plugin-visualizer` or `@next/bundle-analyzer` only if they're already installed.

## Moving filtering to the backend (React)

The usual shape of the problem: `useEffect(() => fetch('/api/items').then(r => r.json()).then(setItems), [])`, then `items.filter(...).sort(...).map(...)` in render.

1. Give the endpoint the filter, sort and cursor parameters, implemented in SQL with the old semantics (see `sql-postgres.md` for the `toLowerCase().includes` and `localeCompare` equivalents).
2. Fetch per filter state:
   - **TanStack Query or SWR installed**: use `useInfiniteQuery` / `useSWRInfinite`, with the filter values in the query key.
   - **Neither**: use a `useEffect` keyed on the debounced filter values, with an `AbortController` that cancels the previous request so a slow old response can't overwrite a newer one.
3. **Debounce** typed input (about 300 ms) with a small `useDebouncedValue` hook. Don't add a library for it.
4. **Load more on scroll** with an `IntersectionObserver` on a sentinel element after the last row, or keep the existing "Load more" button.
5. **Virtualize** when a user can realistically scroll thousands of rows. Use the project's virtualization library if it has one (`@tanstack/react-virtual`, `react-window`, `react-virtuoso`). Otherwise, paginated loading already keeps the first render small. Only add a library when measurement shows deep scrolling is a real use, and say so in the report.
6. **Make stale responses impossible, not unlikely.** Paging plus server filtering creates races: a "load more" request still in flight when the filter changes, a cursor from the old filter used with the new one, an observer that fires between the filter change and the new first page arriving. Keep the filters, cursor and items as one piece of state. Abort every in-flight request (first page and load-more) when the filters change. Tag each request with the filters it was made for, and drop its response if they no longer match. Reset the cursor to null when the filters change, before anything else can read it. `useInfiniteQuery` with the filters in the query key does all of this for you.
7. **Keep the screen identical**: the same markup and classes for rows, and the same empty, loading and error states. Keep the initial sort, and any "N results" text if it exists, by returning a count only when the UI shows one.

## Fetching and rendering

- **Refetching loaded data**: effects with missing or unstable dependencies (objects or arrays created during render), refetching on every mount of a tab, and the same request in two sibling components. Lift the request up, or rely on the query cache with a sensible `staleTime`.
- **Expensive work in render**: filtering or sorting a large array on every keystroke. Once the data is server-filtered this mostly disappears. Otherwise `useMemo` it, keyed on the inputs.
- **Bundles**: load rarely used heavy screens and libraries (charts, editors, PDF, maps) with `React.lazy` and dynamic `import()`. Keep what the first screen needs in the main bundle.

## Node backends

- **Files**: `await pipeline(fs.createReadStream(path), res)` from `node:stream/promises`, not `res.end(await fs.readFile(path))`.
- **Writing large responses**: respect backpressure, with `if (!res.write(chunk)) await once(res, 'drain')`, or stream through `pipeline` with a `Readable.from(asyncGenerator())`.
- **JSON arrays**: write `[`, then each item with `JSON.stringify(item)` separated by commas, then `]`. The output is byte-identical to `JSON.stringify(array)` only if each item's serialization is the same, so check it against the baseline. `res.json(bigArray)` builds the whole string in memory.
- **Postgres rows without a stream library**: a keyset batch loop (`LIMIT 1000` per query, continuing from the last key) bounds memory with plain `pg`. Use `pg-query-stream` or `pg-cursor` if already installed. Release the client in `finally`.
- **node-postgres types**: `COUNT` (`bigint`) and `SUM`/`AVG` (`numeric`) come back as **strings**. If you move a count or sum from JS into SQL, cast in SQL (`COUNT(*)::int`, `SUM(x)::float8` when precision allows) or convert in code, so the JSON output keeps the same numbers.
- **ORMs**: Prisma `findMany({ where, select, take: n + 1, cursor: { id }, skip: 1, orderBy })` gives keyset pagination; use `select` to stop over-fetching, and replace a `findUnique` in a loop with one `findMany({ where: { id: { in: ids } } })`. Drizzle, Kysely and TypeORM have the same building blocks.
- **Concurrent I/O**: `Promise.all` over a mapped array keeps order, but it's unbounded. For large lists, use `p-limit` if it's installed, or a small worker loop over a shared index. `Promise.all` rejects on the first failure, which is the same as a sequential loop that throws.
- **Timeouts**: `fetch(url, { signal: AbortSignal.timeout(10_000) })`.
- **Compression**: `compression()` middleware in Express, or the framework's equivalent, for large JSON. Skip it when a proxy in front already compresses.
