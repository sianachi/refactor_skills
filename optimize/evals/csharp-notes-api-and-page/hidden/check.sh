#!/usr/bin/env bash
# Hidden contract + cost check for the notes API and page. Usage: check.sh <repo-dir> [record]
set -u
here=$(cd "$(dirname "$0")" && pwd); root=$(cd "$here/../../../.." && pwd); . "$root/scripts/pg_eval_lib.sh"
repo=$(cd "$1" && pwd); mode=${2:-}
db=grade_cs_$$; out_dir=$(mktemp -d); port=$((30000 + RANDOM % 9000)); base=http://127.0.0.1:$port
proj=$(find "$repo/src" -name '*.csproj' -not -path '*/obj/*' | head -1)
dotnet publish "$proj" -c Release -o "$out_dir/app" -v q >/dev/null 2>&1 || { echo "build failed"; exit 1; }
create_db "$db"
att=$out_dir/attachments; mkdir -p "$att"; yes "attachment-block-0123456789abcdef" | head -c 157286400 > "$att/7.bin"
(cd "$out_dir/app" && ConnectionStrings__Notes="Host=127.0.0.1;Port=55432;Database=$db;Username=postgres;Password=pg" \
  Notes__AttachmentsPath="$att" exec dotnet "$(basename "${proj%.csproj}").dll" --urls "$base" >"$out_dir/log" 2>&1) & pid=$!
trap 'kill $pid 2>/dev/null; drop_db "$db"; rm -rf "$out_dir"' EXIT
wait_http "$base/api/stats/tags" || { cat "$out_dir/log"; exit 1; }
psql_file "$db" "$here/bigdata.sql" || { echo "bigdata load failed"; exit 1; }
sum=$out_dir/summary.txt
{
measure export_csv "$base/api/export.csv" $pid $db
measure attachment "$base/api/notes/7/attachment" $pid $db
measure attachment_missing "$base/api/notes/8/attachment" $pid $db
measure tag_stats "$base/api/stats/tags" $pid $db
} > "$sum"
q0=$(pgss "$db" calls)
PLAYWRIGHT_CORE="$root/scripts/browser/node_modules/playwright-core/index.mjs" node "$here/browser.mjs" "$base" > "$out_dir/browser.jsonl" || { echo "browser run failed"; exit 1; }
q1=$(pgss "$db" calls)
echo "page_queries|$((q1 - q0))" >> "$sum"
if [ "$mode" = record ]; then cp "$sum" "$here/expected.txt"; cp "$out_dir/browser.jsonl" "$here/expected-browser.jsonl"; cat "$sum"; cut -c1-200 "$here/expected-browser.jsonl"; exit 0; fi
cat "$sum"
python3 - "$here" "$sum" "$out_dir/browser.jsonl" <<'PY'
import json, sys
here, sumf, brf = sys.argv[1:]
exp = {l.split("|")[0]: l.strip().split("|") for l in open(f"{here}/expected.txt")}
got = {l.split("|")[0]: l.strip().split("|") for l in open(sumf)}
fails = []
for k in ("export_csv", "attachment", "attachment_missing", "tag_stats"):
    if got[k][1:4] != exp[k][1:4]: fails.append(f"{k}: response differs (expected {exp[k][1:4]}, got {got[k][1:4]})")
for k in ("export_csv", "attachment", "tag_stats"):  # buffering costs >= 100% of the original's growth; streaming far less
    cap = int(int(exp[k][4]) * 0.4)
    if int(got[k][4]) > cap: fails.append(f"{k}: rss delta {got[k][4]} KB > 40% of original ({cap})")
if int(got["page_queries"][1]) > 60: fails.append(f"page session ran {got['page_queries'][1]} queries > 60")
eb = [json.loads(l) for l in open(f"{here}/expected-browser.jsonl")]
gb = [json.loads(l) for l in open(brf)]
for e, g in zip(eb, gb):
    s = e["step"]
    if g["count"] != e["count"]: fails.append(f"{s}: count text {g['count']!r} != {e['count']!r}")
    n = len(g["items"]) if s == "search:50%" else min(len(g["items"]), len(e["items"]))
    if s == "search:50%" and g["items"] != e["items"]: fails.append(f"{s}: full list differs ({len(g['items'])} vs {len(e['items'])} items)")
    elif g["items"][:n] != e["items"][:n] or (len(e["items"]) and not g["items"]): fails.append(f"{s}: first items differ")
    if g["rendered"] > 500: fails.append(f"{s}: {g['rendered']} rows rendered > 500")
    if g["apiBytes"] > 1_000_000: fails.append(f"{s}: {g['apiBytes']} API bytes > 1MB")
if len(gb) != len(eb): fails.append(f"browser steps {len(gb)} != {len(eb)}")
print("\n".join(fails) if fails else "hidden: all checks pass")
sys.exit(1 if fails else 0)
PY
