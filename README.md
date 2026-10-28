# refactor_skills

Agent skills for refactoring, each in its own folder with a `SKILL.md`, optional `references/`, and an `evals/`
folder of test cases.

| Skill | What it does |
|---|---|
| [debloat](debloat/SKILL.md) | Shrinks code to the least that keeps its behavior. |
| [optimize](optimize/SKILL.md) | Fixes costs that grow with data (streaming, pagination, backend filtering, N+1, indexes) and measures each fix. |

## Install

With the [skills CLI](https://github.com/vercel-labs/skills), for Claude Code, Codex, Cursor and other agents:

```sh
npx skills add sianachi/refactor_skills
```

Or clone and link the skills into Claude Code:

```sh
git clone https://github.com/sianachi/refactor_skills.git
ln -s "$PWD/refactor_skills/debloat" ~/.claude/skills/debloat
ln -s "$PWD/refactor_skills/optimize" ~/.claude/skills/optimize
```

## Testing a skill

Each case in `<skill>/evals/<case>/` has a `prompt.md`, the sample project in `files/`, and graders. Most cases
also hold `hidden/` checks that the run never sees. After a run, grade an iteration folder:

- debloat: `python3 scripts/grade_debloat.py <iteration-dir>`
- optimize: `python3 scripts/grade_optimize.py <iteration-dir>`. The hidden checks need Postgres 17 with
  `pg_stat_statements` on `127.0.0.1:55432` (see `scripts/pg_eval_lib.sh`), and `npm ci` in `scripts/browser`
  for the browser checks.

Or run the cases with `claude plugin eval <skill>`.
