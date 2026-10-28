using Microsoft.EntityFrameworkCore;

namespace Notes.Api.Data;

public class User
{
    public int Id { get; set; }

    public string Name { get; set; } = "";
}

public class Note
{
    public int Id { get; set; }

    public string Title { get; set; } = "";

    public string Body { get; set; } = "";

    public string Tag { get; set; } = "";

    public int AuthorId { get; set; }

    public DateTime CreatedAt { get; set; }
}

public class NotesDb(DbContextOptions<NotesDb> options) : DbContext(options)
{
    public DbSet<User> Users => Set<User>();

    public DbSet<Note> Notes => Set<Note>();

    protected override void OnModelCreating(ModelBuilder b)
    {
        b.Entity<User>().ToTable("users");
        b.Entity<User>().Property(u => u.Id).HasColumnName("id");
        b.Entity<User>().Property(u => u.Name).HasColumnName("name");
        b.Entity<Note>().ToTable("notes");
        b.Entity<Note>().Property(n => n.Id).HasColumnName("id");
        b.Entity<Note>().Property(n => n.Title).HasColumnName("title");
        b.Entity<Note>().Property(n => n.Body).HasColumnName("body");
        b.Entity<Note>().Property(n => n.Tag).HasColumnName("tag");
        b.Entity<Note>().Property(n => n.AuthorId).HasColumnName("author_id");
        b.Entity<Note>().Property(n => n.CreatedAt).HasColumnName("created_at");
        b.Entity<Note>().HasOne<User>().WithMany().HasForeignKey(n => n.AuthorId);
    }
}
