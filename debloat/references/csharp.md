# C# and .NET

Read this before hunting in a C# codebase. It adds to SKILL.md; it doesn't replace any of it.

## Tools

The compiler is your strongest check: after every batch, `dotnet build` must stay warning-for-warning the same, and `dotnet test` green.

| Finds | Command |
|---|---|
| Unused private members, unread fields, unused parameters, unnecessary usings | `dotnet format style --verify-no-changes --severity info --diagnostics IDE0051 IDE0052 IDE0060 IDE0005` |
| Internal classes never instantiated | `dotnet format analyzers --verify-no-changes --severity info --diagnostics CA1812` |
| Unused locals | `dotnet build` warnings CS0168, CS0219 |
| Package references | `dotnet list package`, then search for each package's namespaces |

These report and change nothing with `--verify-no-changes`. They only see private and internal code; for `public` types in an app (not a library), search by name yourself.

## Code that looks dead but runs

.NET wires a lot of code by convention and reflection, so a class with no callers is often alive. Before deleting a type or member, check for:

- **DI registration**: `AddScoped/AddTransient/AddSingleton`, `AddHostedService`, `TryAdd*`, and assembly scanning (Scrutor `.Scan`, `AddMediatR(cfg => cfg.RegisterServicesFromAssembly(...))`, `AddValidatorsFromAssembly`, hand-written `Assembly.GetTypes()` loops). A type found by scanning has no reference by name anywhere: search for the interface it implements, and for `GetTypes`, `IsAssignableFrom` and `Activator.CreateInstance`.
- **Attribute and convention routing**: controllers (`[ApiController]`, the `Controller` suffix), `[HttpGet]`/`[Route]` actions, minimal API `Map*` calls, SignalR hubs, gRPC services, Razor Pages and views, middleware classes with `Invoke`/`InvokeAsync`.
- **Serialization by name**: a property that C# code only ever assigns is still read by `System.Text.Json`, Newtonsoft or a client. Removing it changes the JSON. The same goes for `[JsonPropertyName]`, `[JsonIgnore]`, `[DataMember]`, enum names that appear in payloads, and record positional parameters.
- **Configuration binding**: `Configure<TOptions>(section)`, `Bind`, `IOptions<T>`. Option properties are set by name from appsettings and env vars, so they never show an assignment. Removing or renaming one silently drops the setting.
- **EF Core**: entity properties are columns. `DbSet`s, navigation properties, `OnModelCreating`, `IEntityTypeConfiguration<T>` and everything under `Migrations/` are schema. Never edit or delete a migration. A model change needs a new migration, which is a behavior change: list it instead.
- **Source generators and partial types**: `[LoggerMessage]`, `[JsonSerializable]`, `[GeneratedRegex]`, `partial` declarations whose other half is generated.
- **Visibility beyond the assembly**: `InternalsVisibleTo`, and in a published NuGet library, every `public` and `protected` member is contract.
- **Test-only seams**: an interface with one production implementation and a fake or mock in the tests (Moq, NSubstitute) has two implementations. Keep it when it wraps I/O, time, randomness or an external service. When the "real" class is pure in-memory logic, collapse it and port the tests to use the real class.

## Bloat that's common in C#

- **Interface per class** (`IFooService` + `FooService`, one implementation, no fake): use the class. Change the DI registration to `AddScoped<FooService>()` or `new` it where it's used.
- **Repository over EF Core**: `DbContext` is already a repository and unit of work. A repository that only forwards to a `DbSet` can go; inject the context.
- **MediatR request and handler pairs** that only call a service: call the service. Check first for pipeline behaviors (`IPipelineBehavior<,>`); validation, logging or transactions attached there are behavior and must stay attached.
- **Entity, DTO, view model and mapper** with the same fields (AutoMapper profiles, hand-written `ToDto`): keep the shape the API exposes and drop the copies. Watch the JSON names and the null handling.
- **`Result<T>` wrappers** that are wrapped and unwrapped one layer later, and custom exceptions nobody catches by type.
- **Boilerplate the language now does**: a constructor that only assigns fields (primary constructor), a class with equality code (`record`), braces around single expressions (expression-bodied members), `if (x == null) throw` under `<Nullable>enable</Nullable>` for internal callers (keep it at public and trust boundaries), `return await` in a method that only forwards a `Task`. Use features that the project's `LangVersion` and target framework support. Prefer the ones the codebase already uses somewhere.
- **Constants classes and options** that are never configured differently: inline them, but only if no appsettings, env var or test sets them.

## Building the harness

- **Web API**: run the original (`dotnet run --urls http://127.0.0.1:<port>`, or the built DLL from a copy of the original commit) and the new build side by side, send the same requests with `curl -s -i`, and diff status, headers that clients read (Content-Type, Location) and bodies. `WebApplicationFactory<Program>` in a throwaway test project works too, if the packages are already restored.
- **Library**: a throwaway console project that references the library and prints results and exception types and messages for each case.
- **Error output** is contract: status codes, `ProblemDetails` bodies, validation messages, exception types callers catch.
