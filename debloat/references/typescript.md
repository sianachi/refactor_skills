# TypeScript and JavaScript

Read this before hunting in a TS or JS codebase. It adds to SKILL.md; it doesn't replace any of it.

## Tools

| Finds | Command |
|---|---|
| Unused files, exports, types, dependencies, unlisted deps | `npx knip` (reads the framework config, so it knows Next.js, Vite, Vitest, Storybook entry points) |
| Unused locals and parameters | `npx tsc --noEmit --noUnusedLocals --noUnusedParameters` |
| Unused deps only | `npx depcheck` |

`tsc --noEmit` and the test runner are the check after every batch. Type errors you introduce count as a red batch, even though types don't run.

## Code that looks dead but runs

- **Side-effect imports**: `import "./polyfills"`, `import "./styles.css"`, and modules that register something when loaded (i18n setup, custom elements, `dayjs.extend`). They have no imported names but run code. Never treat them as unused imports.
- **File-based routing and framework conventions**: Next.js `page.tsx`, `layout.tsx`, `route.ts`, `middleware.ts`, `generateMetadata`, `getServerSideProps`; Remix and React Router `loader`/`action`; SvelteKit `+page.ts`; Vite `import.meta.glob`; config files (`vite.config.ts`, `tailwind.config.ts`); Storybook stories; test setup files.
- **Dynamic imports**: `import(\`./locales/${lang}.ts\`)` and `React.lazy(() => import(...))` reach files that no static import mentions.
- **Package surface**: `exports`, `main`, `module`, `types`, `bin` and `files` in package.json. In a published package, every exported value **and type** in the `.d.ts` is contract. Removing an exported type breaks consumers' builds even though no runtime code changes.
- **Decorators and DI**: Angular and NestJS find providers, controllers and modules through decorators; TypeORM and MobX read decorated properties.
- **Ambient code**: `declare global`, `declare module` augmentation and `.d.ts` files change types across the project without being imported.
- **tsconfig paths and aliases**: search for the alias form (`@/lib/x`) as well as the relative path.

## Bloat that's common in TS

- **Types that repeat each other**: an interface for the API response, another for the form, another for the store, all with the same fields. Keep one, and derive the rest with `Pick`, `Omit`, `Partial`, `ReturnType`, `Awaited<ReturnType<...>>`, or `z.infer<typeof schema>` when a zod schema already exists.
- **Types used once**: inline them at the use site, unless they're exported contract or name a real domain concept.
- **Generics with one instantiation**, and type parameters that are never constrained or inferred differently.
- **`enum` plus a lookup object plus a union** for the same set of strings: keep one. A string-literal union with an `as const` array is usually the smallest. Changing a numeric enum changes runtime values: check serialization first.
- **Barrel files** (`index.ts` re-exporting a folder) inside an app: import directly and delete the barrel. Keep the package's own entry barrel.
- **React**: components that only pass props through, custom hooks that wrap one hook call, context with a single consumer, and prop-drilling helpers. Removing `useMemo`, `useCallback` or `React.memo` changes reference identity, which can make effects re-run or children re-render. Keep them unless the harness shows no difference, or no effect or memoized child depends on the value.
- **Classes for stateless logic**: modules of functions are smaller.

## Runtime traps when simplifying

- `??` versus `||`: `0`, `""` and `false` behave differently.
- `structuredClone` versus `JSON.parse(JSON.stringify(x))`: dates, `undefined`, `Map`, class instances and functions all differ.
- Object spread versus `Object.assign`: spread doesn't call setters and copies only own enumerable properties.
- `for...in` includes inherited keys; `Object.keys` doesn't.
- `Array.prototype.sort` without a comparator sorts as strings.
- Optional chaining returns `undefined` where the old code threw. That's a behavior change if a caller relied on the throw.
- Validation schemas (zod, yup, valibot) at API and form boundaries are trust-boundary validation: keep them, including their messages.
