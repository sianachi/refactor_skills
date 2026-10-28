using System.Globalization;
using System.Text;
using Microsoft.EntityFrameworkCore;
using Notes.Api.Data;

namespace Notes.Api.Endpoints;

public record NoteListItem(int Id, string Title, string Excerpt, string Author, string Tag, DateTime CreatedAt);

public record TagCount(string Tag, int Count);

public static class NoteEndpoints
{
    public static void MapNoteEndpoints(this WebApplication app)
    {
        app.MapGet("/api/notes", ListNotes);
        app.MapGet("/api/stats/tags", TagStats);
        app.MapGet("/api/notes/{id:int}/attachment", Attachment);
        app.MapGet("/api/export.csv", ExportCsv);
    }

    static async Task<IResult> ListNotes(NotesDb db)
    {
        var notes = await db.Notes.ToListAsync();
        var items = new List<NoteListItem>();
        foreach (var note in notes.OrderByDescending(n => n.CreatedAt).ThenByDescending(n => n.Id))
        {
            var author = await db.Users.FindAsync(note.AuthorId);
            var excerpt = note.Body.Length > 80 ? note.Body.Substring(0, 80) : note.Body;
            items.Add(new NoteListItem(note.Id, note.Title, excerpt, author!.Name, note.Tag, note.CreatedAt));
        }

        return Results.Ok(items);
    }

    static async Task<IResult> TagStats(NotesDb db)
    {
        var notes = await db.Notes.ToListAsync();
        var stats = notes
            .GroupBy(n => n.Tag)
            .Select(g => new TagCount(g.Key, g.Count()))
            .OrderByDescending(t => t.Count)
            .ThenBy(t => t.Tag, StringComparer.Ordinal)
            .ToList();
        return Results.Ok(stats);
    }

    static async Task<IResult> Attachment(int id, NotesDb db, IConfiguration config)
    {
        var exists = await db.Notes.AnyAsync(n => n.Id == id);
        if (!exists)
        {
            return Results.NotFound();
        }

        var root = config["Notes:AttachmentsPath"] ?? "data/attachments";
        var path = Path.Combine(root, id + ".bin");
        if (!File.Exists(path))
        {
            return Results.NotFound();
        }

        var bytes = await File.ReadAllBytesAsync(path);
        return Results.File(bytes, "application/octet-stream", id + ".bin");
    }

    static async Task<IResult> ExportCsv(NotesDb db)
    {
        var notes = await db.Notes.OrderBy(n => n.Id).ToListAsync();
        var sb = new StringBuilder();
        sb.Append("id,title,tag,author_id,created_at\n");
        foreach (var n in notes)
        {
            sb.Append(n.Id).Append(',')
              .Append('"').Append(n.Title.Replace("\"", "\"\"")).Append('"').Append(',')
              .Append(n.Tag).Append(',')
              .Append(n.AuthorId).Append(',')
              .Append(n.CreatedAt.ToString("yyyy-MM-ddTHH:mm:ssZ", CultureInfo.InvariantCulture)).Append('\n');
        }

        return Results.Text(sb.ToString(), "text/csv");
    }
}
