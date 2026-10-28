---
tags: [skill-creator]
max_turns: 150
timeout_seconds: 3600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

notes app is unusable now that the team has 200k notes. the page takes ages to load and the server memory spikes. optimize everything you can: make it stream, paginate, push the filtering to the backend

A Postgres server is available at postgres://postgres:pg@127.0.0.1:55432 (create your own databases on it).

Input files: the project in this directory.
