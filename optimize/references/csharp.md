# C#, ASP.NET Core and EF Core

Read this when the scope is .NET. It adds to SKILL.md; read `sql-postgres.md` too when the database is Postgres.

## Measuring

- **Queries per request**: turn on `Microsoft.EntityFrameworkCore.Database.Command` logging at `Information` in the harness run, or count with a `DbCommandInterceptor`, or use the Postgres counters from `sql-postgres.md`.
- **Memory**: sample the process RSS (`ps -o rss= -p <pid>`) while a request runs. Use `dotnet-counters monitor -p <pid>` if it's installed. In a test, `GC.GetTotalAllocatedBytes(true)` before and after.
- Run the app in `Release` (`dotnet run -c Release`) when timing.

## EF Core reads

- **Filter before materializing.** `(await db.Notes.ToListAsync()).Where(...)` loads the table; `db.Notes.Where(...).ToListAsync()` doesn't. The same goes for `.Count()`, `.Any()`, `.Sum()`, `.OrderBy()`, `.Skip()/.Take()` and `GroupBy`: put them before `ToListAsync`, so they run in SQL. EF Core 7+ translates `GroupBy` followed by aggregates.
- **Project instead of loading entities**: `.Select(n => new NoteListItem(n.Id, n.Title, n.Author.Name))` reads only those columns and needs no `Include`. It's the biggest win for list endpoints with large text columns.
- **`AsNoTracking()`** on read-only queries, unless the context is already configured with `QueryTrackingBehavior.NoTracking`. Projections into non-entity types are untracked anyway.
- **N+1**: `FindAsync` or a query inside a `foreach` over results, or lazy-loading proxies touching navigations in a loop. Use a projection, `Include`, or one query with `ids.Contains(x.Id)`, which EF translates to `= ANY(@ids)` on Npgsql.
- **Cartesian explosion**: `Include`-ing two collections multiplies rows. Use `.AsSplitQuery()` or a projection.
- **String matching with old client semantics**: `n.Title.ToLower().Contains(q.ToLower())` translates to `strpos(lower(title), lower(@q)) > 0` on Npgsql, a case-insensitive substring match with no escaping needed. `EF.Functions.ILike(n.Title, pattern)` needs `%`, `_` and `\` escaped in the pattern. `string.Contains(q, StringComparison.OrdinalIgnoreCase)` isn't translated. Check where .NET's `ToLowerInvariant` and Postgres `lower()` disagree on non-ASCII input.
- **Keyset pagination**: write the comparison out so every provider translates it:
  ```csharp
  query = query.Where(n => n.CreatedAt < c.CreatedAt || (n.CreatedAt == c.CreatedAt && n.Id < c.Id))
               .OrderByDescending(n => n.CreatedAt).ThenByDescending(n => n.Id)
               .Take(limit + 1);
  ```
  Npgsql can also translate row-value comparisons with `EF.Functions.LessThan(ValueTuple.Create(n.CreatedAt, n.Id), ValueTuple.Create(c.CreatedAt, c.Id))`, which plans better. Verify the generated SQL with `ToQueryString()`.
- **Streaming large result sets**: `AsAsyncEnumerable()` with `await foreach` reads row by row. Combine it with `AsNoTracking()`, or the change tracker keeps every row alive.

## ASP.NET Core responses

- **Return `IAsyncEnumerable<T>`** from a controller action or minimal API. System.Text.Json writes the array as items arrive instead of buffering a `List<T>`. The JSON is the same as before, so it keeps an unchanged contract.
- **CSV or other text exports**: write to `Response.Body` yourself:
  ```csharp
  Response.ContentType = "text/csv";
  await using var writer = new StreamWriter(Response.Body);
  await foreach (var row in query.AsNoTracking().AsAsyncEnumerable()) { await writer.WriteLineAsync(Format(row)); }
  ```
  Validate parameters and run anything that can fail with a clean error (auth, existence checks, opening the query) before the first write. After that the status code is committed. The old string-building code's line endings, quoting and encoding (including whether it wrote a BOM) are part of the output: match them byte for byte.
- **Files**: replace `File.ReadAllBytesAsync` and `return File(bytes, type)` with `PhysicalFile(path, type, enableRangeProcessing: true)`, or `File(new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read, 81920, useAsync: true), type)`. For blobs from storage, return the SDK's stream.
- **Request bodies**: for large uploads, read `Request.Body` or use `MultipartReader` instead of binding to `byte[]` or `IFormFile` with `CopyToAsync(MemoryStream)`.
- **Outbound HTTP**: `HttpClient.GetAsync(url, HttpCompletionOption.ResponseHeadersRead)` then `ReadAsStreamAsync()` streams a large download; the default buffers the whole body. Set `HttpClient.Timeout` or pass a cancellation token with a timeout.
- **Compression**: `AddResponseCompression()` for large JSON. Keep `EnableForHttps` at its default (`false`) unless no response mixes secrets with user-controlled input (BREACH).
- **Pagination parameters**: `[FromQuery] int limit = 50` clamped with `Math.Clamp(limit, 1, 200)`, `[FromQuery] string? cursor`. Decode the cursor in a `try`, and answer a malformed one with the project's usual 400 response.

## Migrations for indexes

Add a new migration (`dotnet ef migrations add AddNoteIndexes`). For Postgres, write the index as raw SQL so it builds concurrently:

```csharp
protected override void Up(MigrationBuilder b) =>
    b.Sql("CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_notes_created_id ON notes (created_at DESC, id DESC);", suppressTransaction: true);
protected override void Down(MigrationBuilder b) =>
    b.Sql("DROP INDEX CONCURRENTLY IF EXISTS ix_notes_created_id;", suppressTransaction: true);
```

Also declare the index in the model (`HasIndex(...)`), so the snapshot knows about it and a later migration won't try to recreate it. If the project creates its schema with `EnsureCreated()` instead of migrations, add the index to the model and note in the report that existing databases need it created by hand.

## Concurrency

- **A `DbContext` is not thread-safe.** Never run two queries on the same context concurrently (`Task.WhenAll` over queries on one context throws or corrupts state). Combine them into one query, run them sequentially, or use a separate context per task from `IDbContextFactory<T>`.
- Bound concurrent outbound calls with `Parallel.ForEachAsync(items, new ParallelOptions { MaxDegreeOfParallelism = 8 }, ...)` or a `SemaphoreSlim`, and write results into an array by index to keep the order.
