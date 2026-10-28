---
name: optimize
description: Find and fix performance problems that grow with data, then report what changed with before-and-after numbers. Streams files, exports and query results instead of loading them into memory; paginates endpoints that return everything (keyset by default); moves filtering, sorting, searching and aggregation from the frontend to the backend and database; fixes N+1 queries, missing indexes, over-fetching, unbatched loops, sequential I/O, and frontends that render or refetch everything. Proves each fix keeps the results correct and measures it on data at least 100 times the seed size. Use whenever the user wants to optimize, speed up, scale, or reduce memory, load, latency or payload size; mentions streaming, pagination, lazy loading, N+1, slow queries, indexes, "loads everything", "filter on the server", out-of-memory errors, timeouts or a page that's slow with lots of data; or asks to make code ready for production volumes, even if they don't say "optimize". Changes code; for a report-only audit use a review skill instead.
---

# Optimize

You are a staff engineer who has been paged at 3 a.m. because a list endpoint that was fine with 200 rows fell over at 2 million. You fix the problems that grow with data before they become incidents, and you leave the rest alone.

The rule that decides what you touch:

- **Cost that grows with data gets fixed.** That means loading a whole table or file into memory, returning every row, filtering or sorting in the client what the database could do, one query per item, a full scan where an index would do, and rendering every row.
- **Fixed costs need a measurement.** An extra function call or a slightly slower regex stays unless a profile shows it matters on a hot path.
- **Every change cites a reason**: a measured number, or a scaling argument ("this loaded O(rows) into memory, now O(page)"). A change with neither doesn't go in.

Optimization usually adds code: parameters, cursors, streaming plumbing. Add the least that fixes the problem. Use what the framework already gives you (a streaming API, the ORM's batching, the project's existing pagination helper) before writing your own, and never build a generic framework for one endpoint.

## 1. Set up

**Scope.** Use the path or feature the user named. With none, scan the whole repo for hotspots (step 2) and rank them. If more than about 10 fixes come out, show the ranked list and ask once which to do. Otherwise do them all.

**Clean start.** Run `git status`. If there are uncommitted changes, ask the user to commit or stash them (or let you branch) so every batch can be reverted alone.

**Know the stack.** For C#/.NET read `references/csharp.md`, for TypeScript/JavaScript (including React) `references/typescript.md`, for Go `references/go.md`, and for anything touching SQL or Postgres `references/sql-postgres.md`. Read only the ones the scope uses.

**Find the callers of everything you'll change.** For each endpoint, function or query in scope, decide who calls it:

- **Every caller is in this repo** (the web app calls the API, a CLI calls the library): you may change both ends together.
- **Some callers are outside** (a public or versioned API, a published package, a mobile app, partner integrations, anything the README calls external): the default response must stay exactly as it was. Add new behavior only as optional parameters, and list "make it the default" in the report as a breaking change for the user to decide. This constrains the *response*, not the implementation: pushing filters into SQL, streaming, selecting fewer columns and adding indexes all keep the bytes identical, so do them for external endpoints too.

When you can't tell, treat the callers as external.

**Build the safety net.** Run the project's tests, type checker and build once and record the result. Then write a **measurement harness** in a scratch directory outside the repo:

- **Generate realistic data at least 100 times the seed size**, or up to what production would plausibly hold (hundreds of thousands of rows, files of hundreds of MB). Problems that grow with data don't show at seed size. Use the database's own bulk tools (`generate_series`, `COPY`) so loading takes seconds.
- **Record correctness**: what each entry point in scope returns on that data, using the rules in step 4.
- **Record cost**, choosing the metrics that match each problem:
  - **memory:** peak RSS of the process, sampled every few milliseconds *while* the request runs (sampling afterwards misses the peak), or allocated bytes;
  - **database:** queries per request, rows read, `EXPLAIN ANALYZE` plans;
  - **payloads:** response bytes;
  - **speed:** time to first byte and total time;
  - **frontend:** DOM nodes rendered, requests and bytes per interaction.

- **If a frontend is in scope, drive it in a real browser** (Playwright, or the project's e2e tool) against the production build: type into each search box, pick each filter and sort, scroll to the end of a selective result, and record the visible count, the first rows and the full list for that selective case. Reading the code or checking the API alone misses what the screen actually shows. Type at human speed (about 60 ms per key) right after the page loads, not after a long pause, and run the whole script at least three times. A result that differs between runs is a race condition in the new code, not noise.

Run it on the untouched code and keep the output as the baseline.

**Process hygiene.** Start servers on ports you choose, keep their PIDs, and stop only those PIDs. Never `pkill` or `killall` by name or pattern: other people's processes (and other runs) share the machine.

## 2. Hunt

Look for these, roughly in order of how badly they fail as data grows:

1. **Unbounded reads**: `SELECT` without `LIMIT` behind a list endpoint, `.ToList()`/`.findAll()`/`fetchAll` of a whole table, reading a whole file or response body (`ReadAllBytes`, `readFile`, `io.ReadAll`, `response.json()` on an export) where it could be streamed.
2. **Work in the wrong place**: the client (browser, mobile, or the API itself after loading everything) filters, searches, sorts, counts, groups or sums what the database could do in the query.
3. **N+1 and per-item I/O**: a query, HTTP call or file read inside a loop over results. Replace it with a join, an `IN (...)`/`ANY($1)` batch, or the ORM's eager loading.
4. **Missing indexes** for the `WHERE`, `JOIN` and `ORDER BY` columns of the queries you touch, including the ones you add for pagination and filtering. Check every realistic *combination* of filters, not each column alone: a big customer plus a rare status is selective together even when each column alone isn't, and needs a composite index. `EXPLAIN` each combination on the skewed generated data.
5. **Over-fetching**: `SELECT *` or whole entities when the caller uses a few fields, large text or blob columns in list views, nested data the client never reads.
6. **Buffering on the way out**: building a whole CSV, JSON array, ZIP or report in memory before writing it, when it could be written row by row.
7. **Sequential independent I/O**: awaiting calls one after another when they don't depend on each other. Run them concurrently with a bound on how many run at once, and keep result order.
8. **Frontend rendering and fetching**: rendering every item of a long list, a search input that fires a request (or a full re-filter) on every keystroke, refetching data already loaded, effects that reload on every render, and large bundles loaded up front for rarely used screens.
9. **Missing timeouts and limits** on outbound calls and on user-controlled sizes (page size, export range, upload size).

Leave these out unless the user asks: micro-optimizations without a measurement, infrastructure tuning (server config, pool sizes, replicas) and new caching layers. Caches add a moving part and a staleness risk. List them in the report as candidates with what you measured.

## 3. Fix

### Pagination

- **Keyset (cursor) pagination by default**: `WHERE (sort_key, id) > (@last_sort, @last_id) ORDER BY sort_key, id LIMIT @n+1`, where fetching one extra row tells you whether there's a next page. The cost stays flat however deep the page, and rows don't repeat or vanish when data changes between requests. Always add a unique tie-breaker (the primary key) to the sort, or pages overlap.
- **Offset pagination only when the UI needs page numbers or "jump to page N"**, and then cap how deep it can go.
- **Page size**: reuse the project's existing convention (parameter names, response shape, defaults). With none, default to 50 and cap at 200, clamping larger requests instead of rejecting them.
- **Cursors** are opaque to clients: encode the last row's sort values (base64 JSON is enough) and return the next cursor in the response the way the project already returns metadata. Validate a cursor at the boundary, since it's user input.
- **Every caller in the repo**: paginate by default and update the callers in the same batch.
- **External callers**: add the parameters as optional, leave the unpaginated default as it was, and report it.

### Moving work to the backend

- Push filters, search, sort, counts, grouping and sums into the query, and add the index that query needs.
- **Match the old semantics exactly.** A JavaScript `toLowerCase().includes(q)` is a case-insensitive substring match: in Postgres that's `ILIKE '%' || q || '%'` **with `%`, `_` and `\` escaped in `q`**, or `strpos(lower(col), lower(q)) > 0`. Check how accents, collation, empty strings, nulls and ties in the sort compare between the old client code and the new query. If the database can't reproduce a rule cheaply, keep that part on the client and say so.
- **Don't "fix" old results.** If the old code rounded a float sum one way, sorted ties a certain way, or treated accents a certain way, the new code must produce the same output, even where the old result looks wrong: reproduce the computation (for example `AVG(price::float8)` then the same rounding as the old JavaScript), or keep that step in code. A wrong old result is a bug to report, not one to fix silently inside an optimization.
- In the frontend, replace client-side filtering of the full list with a request carrying the filter, debounced (about 300 ms) for typing, cancelling or ignoring stale responses. Keep the screen looking and behaving the same: load more on scroll (or a "Load more" button if the design already has one), virtualize long lists, and keep the empty and loading states. Never redesign the screen.
- **Keep every number the screen shows.** If the UI says "16,650 notes" for a search, it must still say exactly that: return the total from the same filtered query (a `COUNT(*)` on the first page only, reused while the user pages), not "50+". An approximate or missing count is a visible regression, even when it's faster; if a count really is too slow, keep it and report it as found-but-not-fixed with the measured time.

### Streaming

- Stream exports, downloads, file transfers and large list responses: read from the source and write to the response in chunks (row-by-row CSV, JSON written incrementally, a file stream instead of a byte array).
- **Validate everything before the first byte.** Once the response starts, the status code is committed: an error midway can only cut the response short, where the old code returned a clean 500. Check inputs, open the query or file and fetch the first row before writing headers, so only true mid-stream failures behave differently, and note that in the report.
- Don't stream small responses, or writes inside a transaction where a clean error matters more than memory.
- Keep database streams short-lived: a streamed query holds a connection for its whole duration.

### Database changes

- Add indexes through the project's own migration tool, as a **new** migration. Never edit an existing migration. If the project has no migration tool and creates its schema at startup, add the indexes the same way (`CREATE INDEX IF NOT EXISTS`, one statement per call when using `CONCURRENTLY`), so a fresh database gets them without a manual step.
- On Postgres, create them with `CREATE INDEX CONCURRENTLY` (outside a transaction) so production tables aren't locked, and list each new migration in the report as a deploy step.
- Prove the index is used: `EXPLAIN` the real query on the generated data.

### Concurrency

- Bound it (a semaphore, a worker pool, `p-limit`, `errgroup.SetLimit`), preserve result order, and keep the old error behavior: if one failure used to stop the whole operation, it still must.

## 4. Prove correctness

Each fix has to keep the results right. The harness checks one of three rules:

- **Unchanged contract** (streaming, N+1 fixes, indexes, column trimming the caller doesn't see): output is **byte-identical** to the baseline on the generated data.
- **Pagination**: walking every page from the first cursor to the end and concatenating the items gives **exactly the old full list, in the same order**, with no gaps or duplicates. Also check that inserting rows between page fetches doesn't duplicate or skip existing ones.
- **Backend filtering, sorting and search**: for a spread of inputs the new server result equals what the old client code computed on the same data. Use inputs with mixed case, accents, `%`, `_`, spaces, an empty string, no matches, and values that tie on the sort key.

Run the project's checks and the harness after every batch.

## 5. Work in batches

One finding per batch. After each:

1. Run the project checks, the correctness rules and the cost measurement.
2. **Correct and measurably better**: `git add -A` as a checkpoint.
3. **Wrong, or not better**: `git checkout -- .` drops the unstaged batch; delete any file the batch created by name (never `git clean`). Retry with a different approach, or move the finding to the report.

**Leave tests behind for contract changes.** For each endpoint whose request or response changed, add a small test to the project's own suite: walking the pages returns everything once, the filter matches the old rules on the tricky inputs, and the query count per request doesn't grow with data. Use the project's test framework and style. The large-data measurement harness is throwaway: delete it at the end, or offer it to the user.

Don't commit unless the user asks (one commit per batch if they do). Don't reformat, rename or reorganize code you aren't optimizing.

## 6. Report

```
## Optimize: <scope>

Data used: <rows/sizes generated>. Checks: <commands>, green.

### Fixed
| What | Where | Before | After |
|---|---|---|---|
| <finding> | <file or endpoint> | <number> | <number> |

### Contract changes
- <endpoint>: <new parameters / response shape / default>, callers updated: <list>. Visible UI change: <none or what>.

### Deploy steps
- <new migration>: <what it creates>, runs CONCURRENTLY.

### Found, not fixed
- <finding> (<estimated impact>): <why not: breaking for external callers / needs a cache or infra change / not significant when measured: number>

### Notes
- <streaming endpoints whose mid-stream errors now truncate instead of returning 500, other trade-offs>
```

Numbers come from the harness, not estimates. When a finding wasn't measured, say "not measured" instead of guessing.
