#!/usr/bin/env bash
# Hidden contract + cost check for the Go orders service. Usage: check.sh <repo-dir> [record]
set -u
here=$(cd "$(dirname "$0")" && pwd); . "$here/../../../../scripts/pg_eval_lib.sh"
repo=$(cd "$1" && pwd); mode=${2:-}
db=grade_go_$$; bin=$(mktemp -d)/orders; port=$((21000 + RANDOM % 9000)); base=http://127.0.0.1:$port
(cd "$repo" && go build -o "$bin" .) || { echo "build failed"; exit 1; }
create_db "$db"
(cd "$repo" && DATABASE_URL=$(db_url "$db") PORT=$port exec "$bin" >/tmp/orders-$$.log 2>&1) & pid=$!
trap 'kill $pid 2>/dev/null; drop_db "$db"; rm -f /tmp/orders-$$.log' EXIT
wait_http "$base/orders?customer_id=-1" || { cat /tmp/orders-$$.log; exit 1; }
psql_file "$db" "$here/bigdata.sql" || { echo "bigdata load failed"; exit 1; }
out=$(mktemp)
{
measure export_all "$base/export/orders.csv" $pid $db
measure export_returned "$base/export/orders.csv?status=returned" $pid $db
measure summary_big "$base/customers/1/summary" $pid $db
measure summary_small "$base/customers/4242/summary" $pid $db
measure summary_missing "$base/customers/99999/summary" $pid $db
measure summary_bad "$base/customers/abc/summary" $pid $db
measure list_filtered "$base/orders?status=returned&customer_id=1" $pid $db
measure list_customer "$base/orders?customer_id=4242" $pid $db
measure list_bad "$base/orders?customer_id=x" $pid $db
measure list_all "$base/orders" $pid $db
} > "$out"
idx_items=$(psql_q "$db" "EXPLAIN SELECT * FROM order_items WHERE order_id = 5" | grep -cE "Index|Bitmap")
idx_cust=$(psql_q "$db" "EXPLAIN SELECT id FROM orders WHERE customer_id = 4242" | grep -cE "Index|Bitmap")
echo "index|order_items.order_id=$idx_items|orders.customer_id=$idx_cust" >> "$out"
if [ "$mode" = record ]; then cp "$out" "$here/expected.txt"; cat "$out"; exit 0; fi
cat "$out"
python3 - "$here/expected.txt" "$out" <<'PY'
import sys
exp = {l.split("|")[0]: l.strip().split("|") for l in open(sys.argv[1])}
got = {l.split("|")[0]: l.strip().split("|") for l in open(sys.argv[2])}
fails = []
for k, e in exp.items():
    if k == "index": continue
    g = got.get(k)
    if not g or g[1:4] != e[1:4]: fails.append(f"{k}: response differs (expected {e[1:4]}, got {g[1:4] if g else None})")
lim = {"export_all": ("rss", 40000), "summary_big": ("queries", 10), "summary_small": ("queries", 10), "list_filtered": ("blocks", 3000)}
col = {"rss": 4, "queries": 5, "blocks": 6}
for k, (m, cap) in lim.items():
    v = int(got[k][col[m]])
    if v > cap: fails.append(f"{k}: {m} {v} > {cap}")
idx = got["index"]
if any(p.endswith("=0") for p in idx[1:]): fails.append(f"index not used: {idx[1:]}")
print("\n".join(fails) if fails else "hidden: all checks pass")
sys.exit(1 if fails else 0)
PY
