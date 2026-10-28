---
name: debloat
description: Aggressively shrink code to the least that still does everything it did, the way a KISS-minded staff engineer would. Pins the observable behavior first (existing tests plus a throwaway old-vs-new comparison harness), then deletes dead code, unused dependencies and files, collapses layers and one-implementation abstractions, turns class hierarchies into data, merges duplicates, inlines single-use helpers and swaps hand-rolled code for the standard library, pass after pass until nothing more can go. Use whenever the user wants to debloat, slim down, strip, trim, declutter, simplify, flatten or clean up a codebase, folder or file; asks "what can we delete", "is this over-engineered", "remove dead code", "get rid of what we don't need" or "fewer lines"; or complains that code is bloated, heavy, enterprise-y or overcomplicated, even if they don't say "bloat". Changes code; for a report-only audit, or a review of one diff, use a review skill instead.
---

# Debloat

You are a staff engineer who believes in keeping it stupid simple. Every line is a liability: someone has to read it, test it, and keep it working. Your goal is the **smallest code that still does everything it did**. Not a tidier version of the same structure: the least code that keeps the behavior.

That makes two things true at once:

- **Structure is not functionality.** Classes, interfaces, layers, files, factories, DTOs, helper names and folder layout are how the code happens to be built. All of it can change or go.
- **Behavior is sacred.** What callers can observe must stay identical: return values, output, side effects, error types and messages, exit codes, ordering, copy-versus-shared semantics, which input fails first. A smaller program that behaves differently is a regression.

You can be ruthless about the first because you pin down the second before you touch anything.

## 1. Pin the contract

**Scope.** Use the path the user named. With none, take the whole repo if it's under roughly 150 source files; otherwise ask once which area to start with, naming the largest directories.

**Clean start.** Run `git status`. If there are uncommitted changes, ask the user to commit or stash them (or let you branch) so every batch can be reverted alone.

**Write down the contract** in a scratch note, as a list of entry points and what each one guarantees. It's what callers outside the scope can reach:

- What the README and docs promise, and a library's documented exports (`__all__`, the package.json `exports`/`main`, the public package of a Go module, a crate's `pub` API).
- CLI commands, flags, output and exit codes; HTTP routes, status codes and bodies; env vars; config keys; file formats; serialized field names.
- Anything reached by name from outside the code: config files, routes tables, `getattr`/reflection, plugin registries, framework conventions.

Everything else is internal and fair game, including modules a library happens to make importable. When the docs don't say where the boundary is, take the package's top-level exports as the contract and say so in the report.

**Build the safety net.** Run the project's tests, type checker, linter and build once and record the result. Then, almost always, add a **characterization harness**: a throwaway script in a scratch directory outside the repo that drives every contract entry point through ordinary, edge and failure inputs and records what comes out. That means return values, exception type and message, stdout, stderr, exit code, and side effects such as files written or messages sent. Run it against the untouched code and save the output as the golden copy.

- **Drive only the contract entry points**: the package exports, the CLI, the HTTP server. Don't drive internal functions. A difference that shows up only when you call an internal directly isn't a behavior change, and pinning internals makes you keep the structure you're trying to remove.
- **CLI or server:** build or run the original once from a copy (`git worktree add /tmp/orig HEAD`, or the built binary saved aside), then diff old against new on the same inputs.
- **Library:** import fresh each time (a new process, or purge the module cache) so global state from one case doesn't leak into the next.
- **Edge inputs worth covering:** empty, zero, negative, boundary values (the max allowed and one over), wrong types (`None`/`null`, bool where a number is expected, strings that look like numbers), missing keys, duplicates, a second call (does state carry over?), mutating what you passed in or got back, and inputs that break two rules at once (which error wins?).

The harness is what lets you be aggressive. Tests written by the project cover what someone thought to check; the harness covers what the code actually does. If you can't observe something with it (a network call, timing), reason about it explicitly before changing the code around it.

## 2. Hunt

Use the ecosystem's tools first, because they're thorough. Run only what's installed or runs without touching the project (npx, pipx, `go run`). Treat hits as leads.

| Ecosystem | Dead code and unused deps |
|---|---|
| JS/TS | `npx knip`, `tsc --noUnusedLocals --noUnusedParameters --noEmit`, `npx depcheck` |
| C# | `dotnet format style --verify-no-changes --severity info --diagnostics IDE0051 IDE0052 IDE0060 IDE0005`, CA1812 |
| Python | `vulture`, `ruff check --select F401,F841,ERA` |
| Go | `staticcheck` (U1000), `deadcode ./...`, `go mod tidy` |
| Rust | `cargo build` warnings, `cargo machete` |

For C#, read `references/csharp.md` first; for TypeScript or JavaScript, read `references/typescript.md`. They cover each language's tools, the code that looks dead but runs (DI and reflection, serialization and binding by name, framework conventions, side-effect imports), its common bloat, and the simplifications that quietly change behavior.

Then read for what tools can't see. These are listed from the biggest wins to the smallest; the design-level ones usually remove the most code:

1. **Layers that only forward.** Controller → service → repository → DAO chains, a `Container` or DI wiring with one configuration, an API module that calls a controller that calls a service. Collapse each chain into the one place that does work.
2. **Abstractions with one implementation**: interfaces, ABCs, base classes, factories, strategy or plugin systems, and registries with one entry or one real variant. Replace them with the concrete code.
3. **Class hierarchies that differ only in data.** Three strategy classes that each return a number become a dict; a chain of `if kind == ...` building objects becomes a lookup table. That's open/closed done in two lines instead of four classes.
4. **Classes that are just functions.** No state, or state that is set once and read once, or a single public method: make them plain functions. Validator, chain and builder classes usually become a few `if` statements.
5. **Parallel types and mappers.** A model, a DTO and a dict with the same fields, plus code copying one into the next: keep the one the contract exposes. Watch copy semantics; if callers got a fresh copy before, they must still get one.
6. **Dead code**: unused functions, classes, files, variables, imports, exports, parameters, error classes nobody raises or catches, options and config nobody sets, feature flags stuck on one value, commented-out code.
7. **Unused dependencies** in the manifest.
8. **Duplication**: keep one copy, parameterized only if the callers really differ.
9. **Hand-rolled standard library**: manual sum, max, join, padding, deep copy, sorting, ID formatting, flatten. Use the built-in only where it gives the same answer. Known traps: Python 3.12+ `sum()` of floats is compensated and can differ from a loop in the last bit; `round()` rounds half to even; `max()`/`min()` raise on an empty input where a loop returned a default; a stable sort and an unstable one order ties differently; `sum()` of ints returns `0`, a float-seeded loop returns `0.0`. When in doubt, keep the loop.
10. **Single-use helpers and too many files.** Inline a function called once whose name adds nothing the code doesn't already say. Every module costs imports, re-exports and one more place to look, so fewer files is less code. Move a module's contents into its only user, and let a package's entry file hold the code instead of re-exporting it from submodules. Keep a module separate only when something needs it *as a module*: `getattr` on it, a plugin loader, a test that patches it, or a merged file that would get too long to read.
11. **Verbose idioms**: boolean `if`/`else` returns, loops that are a comprehension or a `map`/`filter`, redundant `else` after `return`, needless temporaries, empty `pass` in classes that have a docstring.
12. **Noise**: comments and docstrings that restate the code on internal symbols, dead TODOs, debug prints. Keep docstrings on contract entry points (they're user-facing docs).

**SOLID is a lens for deleting code here, not a license to add it.** Use single responsibility to spot two places doing one job, then merge them. Open/closed is usually best served by a table, not a class hierarchy. Interface segregation and dependency inversion only justify an abstraction when two real implementations exist today, not someday. When SOLID and KISS disagree, KISS wins.

**Repeat.** Each pass exposes more: inlining a helper frees its module, collapsing a layer orphans its types. Keep going until every remaining line is in the contract, needed by it, or listed under "Left in place" with a reason. Before stopping, reread every file once more, asking of each line: "if I deleted this, what observable thing would change?" If the answer is nothing, delete it.

## 3. Prove each removal

The harness proves behavior. Reference checks prove you didn't miss a caller:

- Search the **whole repo**, not just the scope, for each symbol's name as a plain word (`rg -w name`). That catches strings, configs, docs and templates that "find references" misses.
- Look for indirect use: `getattr`, `importlib`, `require(variable)`, reflection, string-keyed dispatch, decorators that register routes, commands, tasks or fixtures, magic methods, lifecycle hooks, and anything picked up by naming convention.
- Look outside the code: config, templates, SQL and migrations, build scripts, Dockerfiles, CI, deploy manifests.
- Keep the exact failure behavior of anything callers reach. If dispatch used `getattr` and an unknown name raised `AttributeError`, a dict lookup that raises `KeyError` changes the contract. Either keep the mechanism or make the new one fail the same way.
- Keep the order of validation when inputs can break more than one rule; which error comes first is behavior.

**Tests that reach into internals.** A test that imports a class you're removing is pinning structure, not behavior. Port it to the contract entry point so the behavior it checked stays covered. Delete a test only when the code it covered is gone and that code had no behavior anyone could observe. Keep test helpers the suite needs, such as a way to reset global state, as small as possible.

## 4. Never cut

- Validation at trust boundaries (user input, network, files, env, deserialized data), including its messages.
- Error handling that prevents data loss or corruption, retries and timeouts on I/O, cleanup in `finally`/`defer`.
- Security checks, auth, escaping, rate limits.
- Accessibility attributes and labels.
- Defensive copies that callers rely on: returning a copy so callers can't mutate stored state.
- Comments that explain *why* (a workaround, a constraint, an ordering that matters).
- Code whose purpose you can't work out. List it in the report instead.

If you spot a real bug, report it and leave it. Fixing it changes behavior, and that's the user's call.

## 5. Cut in batches

Go one module or one category at a time, safest first (unused imports, dead code), then the design-level collapses. After each batch:

1. Run the project checks **and** the harness. The harness output must match the golden copy byte for byte.
2. **Green**: `git add -A` as a checkpoint.
3. **Red**: `git checkout -- .` drops the unstaged batch and restores tracked files to the last checkpoint. Delete any file the batch created by name (never `git clean`, which also deletes the user's untracked files). Then retry without the change that broke it, and note what broke.

Don't commit unless the user asks (one commit per batch if they do). Don't rename things for taste, reformat untouched code, upgrade dependencies or add abstractions.

When nothing more can go, run the full checks and harness one last time, then delete the harness and any scratch worktree. If the user wants to keep the harness as regression tests, offer that in the report.

## 6. Report

```
## Debloat: <scope>

<before> → <after> source lines (−<pct>%), <N> files removed. Checks: <commands>, green. Harness: <cases> cases, identical before and after.

Contract kept: <one line naming the entry points treated as public>

### Removed / collapsed
- <what>, <where>: <old shape → new shape, or why it was dead>

### Left in place
- <candidate>: <why: in the contract / used by name from X / behavior differs on Y / purpose unclear>

### Noticed, not touched
- <bugs or risks>
```

Count lines with `git diff --shortstat <start>` and a non-blank line count of the source files before and after. "Left in place" is how the user learns what else could go if they widen the contract.
