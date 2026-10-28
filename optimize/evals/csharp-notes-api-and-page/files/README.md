# Notes

Team notes app: an ASP.NET Core API on Postgres and the single page in `wwwroot/` that is its only client.

    ConnectionStrings__Notes="Host=...;Database=...;Username=...;Password=..." \
      dotnet run --project src/Notes.Api --urls http://127.0.0.1:5090

EF Core migrations in `src/Notes.Api/Migrations` run at startup. `db/seed.sql` loads a small dev dataset;
attachments live under `data/attachments/<noteId>.bin` (configurable with `Notes__AttachmentsPath`).

The finance team pulls `GET /api/export.csv` nightly with a script that diffs it byte for byte against the
previous night, so its format must not change.
