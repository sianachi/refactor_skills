#!/usr/bin/env bash
# Hidden contract + cost check for the catalog app. Usage: check.sh <repo-dir> [record]
set -u
here=$(cd "$(dirname "$0")" && pwd); root=$(cd "$here/../../../.." && pwd); . "$root/scripts/pg_eval_lib.sh"
repo=$(cd "$1" && pwd); mode=${2:-}
db=grade_ts_$$; work=$(mktemp -d); port=$((40000 + RANDOM % 9000)); base=http://127.0.0.1:$port
rsync -a --exclude node_modules --exclude web/dist --exclude .git "$repo/" "$work/app/"
(cd "$work/app" && npm ci --silent --prefer-offline >/dev/null 2>&1 && npm run build --silent >/dev/null 2>&1) || { echo "install/build failed"; exit 1; }
create_db "$db"
(cd "$work/app" && DATABASE_URL=$(db_url "$db") PORT=$port exec node server/index.ts >"$work/log" 2>&1) & pid=$!
trap 'kill $pid 2>/dev/null; drop_db "$db"; rm -rf "$work"' EXIT
wait_http "$base/" || { cat "$work/log"; exit 1; }
psql_file "$db" "$here/bigdata.sql" || { echo "bigdata load failed"; exit 1; }
sum=$work/summary.txt
{
measure export_json "$base/api/products/export.json" $pid $db
measure category_summary "$base/api/categories/summary" $pid $db
measure api_404 "$base/api/nope" $pid $db
} > "$sum"
q0=$(pgss "$db" calls)
PLAYWRIGHT_CORE="$root/scripts/browser/node_modules/playwright-core/index.mjs" node "$here/browser.mjs" "$base" > "$work/browser.jsonl" || { echo "browser run failed"; tail -5 "$work/log"; exit 1; }
q1=$(pgss "$db" calls)
echo "page_queries|$((q1 - q0))" >> "$sum"
if [ "$mode" = record ]; then cp "$sum" "$here/expected.txt"; cp "$work/browser.jsonl" "$here/expected-browser.jsonl"; cat "$sum"; cut -c1-180 "$here/expected-browser.jsonl"; exit 0; fi
cat "$sum"
python3 - "$here" "$sum" "$work/browser.jsonl" <<'PY'
import json, sys
here, sumf, brf = sys.argv[1:]
exp = {l.split("|")[0]: l.strip().split("|") for l in open(f"{here}/expected.txt")}
got = {l.split("|")[0]: l.strip().split("|") for l in open(sumf)}
fails = []
for k in ("export_json", "category_summary", "api_404"):
    if got[k][1:4] != exp[k][1:4]: fails.append(f"{k}: response differs (expected {exp[k][1:4]}, got {got[k][1:4]})")
cap = int(int(exp["export_json"][4]) * 0.4)  # buffering costs >= 100% of the original's growth; streaming far less
if int(got["export_json"][4]) > cap: fails.append(f"export_json: rss delta {got['export_json'][4]} KB > 40% of original ({cap})")
if int(got["page_queries"][1]) > 80: fails.append(f"page session ran {got['page_queries'][1]} queries > 80")
eb = [json.loads(l) for l in open(f"{here}/expected-browser.jsonl")]
gb = [json.loads(l) for l in open(brf)]
for e, g in zip(eb, gb):
    s = e["step"]
    if g["count"] != e["count"]: fails.append(f"{s}: count text {g['count']!r} != {e['count']!r}")
    if g["options"] != e["options"]: fails.append(f"{s}: category options differ")
    if "all pages" in s:
        if g["items"] != e["items"]: fails.append(f"{s}: full list differs ({len(g['items'])} vs {len(e['items'])} items)")
    else:
        n = min(len(g["items"]), len(e["items"]))
        if g["items"][:n] != e["items"][:n] or (e["items"] and not g["items"]): fails.append(f"{s}: first items differ")
    if g["rendered"] > 500: fails.append(f"{s}: {g['rendered']} rows rendered > 500")
    if g["apiBytes"] > 1_000_000: fails.append(f"{s}: {g['apiBytes']} API bytes > 1MB")
if len(gb) != len(eb): fails.append(f"browser steps {len(gb)} != {len(eb)}")
print("\n".join(fails) if fails else "hidden: all checks pass")
sys.exit(1 if fails else 0)
PY
