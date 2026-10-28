using Microsoft.EntityFrameworkCore;
using Notes.Api.Data;
using Notes.Api.Endpoints;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddDbContext<NotesDb>(o => o.UseNpgsql(builder.Configuration.GetConnectionString("Notes")));

var app = builder.Build();

using (var scope = app.Services.CreateScope())
{
    scope.ServiceProvider.GetRequiredService<NotesDb>().Database.Migrate();
}

app.UseDefaultFiles();
app.UseStaticFiles();
app.MapNoteEndpoints();

app.Run();
