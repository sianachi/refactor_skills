# Go

Read this when the scope is Go. It adds to SKILL.md; read `sql-postgres.md` too when the database is Postgres.

## Measuring

- **Memory**: the peak RSS of the server while a request runs (`ps -o rss= -p <pid>` sampled in a loop), or `/usr/bin/time -l` (macOS) / `-v` (Linux) around a CLI. Inside a test or benchmark, use `testing.B` with `b.ReportAllocs()`, or `runtime.ReadMemStats` before and after.
- **Profiles**: if the service already mounts `net/http/pprof`, use it. Otherwise add it only in the scratch harness copy, not in the repo.
- Build the harness binaries from the original commit (`git worktree add`) and from the working tree, and run both against the same database.

## Streaming

- **Query results**: `rows, err := db.QueryContext(ctx, q, args...)`, then iterate with `for rows.Next()`, scanning and writing each row. Check `rows.Err()` after the loop, and `defer rows.Close()`. With pgx, `pool.Query` plus `rows.Next()` streams, while `pgx.CollectRows` loads everything (fine for one page, wrong for an export).
- **CSV**: `cw := csv.NewWriter(w)`, `cw.Write(record)` per row, then `cw.Flush()` and `cw.Error()` at the end. `csv.Writer` buffers about 4 KB, so memory stays flat. Call `Flush` plus `http.Flusher` every few thousand rows if clients need to see progress.
- **JSON arrays**: write `[`, encode each item with `json.Marshal`, separate with commas, then write `]`. `json.NewEncoder(w).Encode(slice)` builds the whole slice first. Note that `Encoder.Encode` appends a newline: if the old handler used `json.NewEncoder(w).Encode(all)`, the new output must still end with `]\n`.
- **Validate before the first byte**: parse parameters, run the query and check its error before `w.WriteHeader` or the first `Write`. A query error found after writing has started can only end the response early. Log it, and note the change in the report.
- **Files**: `http.ServeContent(w, r, name, modTime, f)` with an `*os.File` (it handles ranges), or `io.Copy(w, f)`. Never `os.ReadFile` a file of unbounded size in a handler.
- **Request bodies**: decode from `r.Body` with `json.NewDecoder`, wrapped in `http.MaxBytesReader` for user-controlled sizes. `io.ReadAll(r.Body)` with no limit is a memory problem and a denial-of-service risk.
- **`COPY ... TO STDOUT`** through pgx (`conn.PgConn().CopyTo(ctx, w, sql)`) is the fastest CSV export, but Postgres CSV quoting and number formatting differ from `encoding/csv` and `strconv`. Use it only when the bytes match the baseline.

## Queries

- **N+1**: replace a query per item with `WHERE id = ANY($1)`, passing a `[]int64` (pgx handles slices; with `lib/pq`, use `pq.Array`), then group the results in a map. A single aggregate query with `GROUP BY` is better when the handler only needs totals.
- **Filtering in Go after `SELECT *`**: move the condition into the `WHERE` with a placeholder, select only the needed columns, and add the index (`sql-postgres.md`).
- **Strings built in loops**: `s += ...` in a loop over rows is quadratic in data size and counts as a problem that grows with data. Use a `strings.Builder`, or write straight to the `io.Writer`.

## Concurrency

- **`errgroup.WithContext` plus `g.SetLimit(n)`** for bounded concurrent I/O, writing each result into a preallocated slice at its index to keep the order. The first error cancels the context and `g.Wait()` returns it, which matches a sequential loop that stops at the first error.
- Never share a `*sql.Tx` or a single pgx connection across goroutines. A `*sql.DB` or `*pgxpool.Pool` is safe to share.

## Timeouts

- Servers: set `ReadHeaderTimeout` at least, and `ReadTimeout`/`WriteTimeout` unless handlers stream for a long time (exports). Clients: `http.Client{Timeout: ...}`, or a context deadline per request. Pass `r.Context()` into queries so an abandoned request stops its query.
