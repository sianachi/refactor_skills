#!/usr/bin/env bash
# Hidden contract: build the API, start it, send fixed requests, compare status, Content-Type, Location and body.
# Usage: check.sh <repo-dir> [record]   (record rewrites expected.txt)
set -u
dir=$(cd "$(dirname "$0")" && pwd); repo=$1; mode=${2:-}
out=$(mktemp -d); proj=$(find "$repo" -name '*.csproj' -not -path '*/obj/*' | head -1)
dotnet build "$proj" -o "$out" -v q >/dev/null 2>&1 || { echo "build failed"; exit 1; }
port=$((20000 + RANDOM % 20000)); base=http://127.0.0.1:$port
(cd "$out" && exec dotnet Catalog.Api.dll --urls "$base" >/dev/null 2>&1) & pid=$!
trap 'kill $pid 2>/dev/null; rm -rf "$out"' EXIT
for _ in $(seq 60); do curl -s "$base/health" >/dev/null && break; sleep 0.25; done
req() { # method path [json]
  local args=(-s -i -X "$1" "$base$2"); [ $# -ge 3 ] && args+=(-H 'Content-Type: application/json' --data "$3")
  curl "${args[@]}" | tr -d '\r' | awk -v m="$1" -v p="$2" '
    NR==1 {status=$2} /^[Cc]ontent-[Tt]ype:/ {ct=$2} /^[Ll]ocation:/ {loc=$2} body {b=b $0} /^$/ && !body {body=1}
    END {gsub(/"traceId":"[^"]*"/, "\"traceId\":\"*\"", b); print m " " p " | " status " | " ct " | " loc " | " b}'
}
{
req GET /health
req GET /products
req GET "/products?page=2&pageSize=2"
req GET "/products?page=0&pageSize=0"
req GET "/products?page=9"
req GET /products/1
req GET /products/99
req GET /products/abc
req GET /products/1/price
req GET "/products/2/price?qty=7"
req GET "/products/1/price?qty=10"
req GET "/products/3/price?qty=1"
req GET "/products/3/price?qty=10"
req GET "/products/1/price?qty=0"
req GET "/products/99/price?qty=0"
req GET /products/99/price
req POST /products '{}'
req POST /products '{"name":"  "}'
req POST /products '{"name":"Lamp"}'
req POST /products '{"name":"Lamp","sku":"x"}'
req POST /products '{"name":"Lamp","sku":"x","unit_price":-1}'
req POST /products '{"name":"Lamp","sku":"x","unit_price":"abc"}'
req POST /products 'not json'
req POST /products '{"name":" Desk Lamp ","sku":" clr-9 ","unit_price":20.5}'
req GET /products/4
req GET "/products/4/price?qty=10"
req GET "/products?page=2&pageSize=50"
req DELETE /products/1
} > "$out/actual.txt"
if [ "$mode" = record ]; then cp "$out/actual.txt" "$dir/expected.txt"; cat "$dir/expected.txt"; exit 0; fi
if diff "$dir/expected.txt" "$out/actual.txt" > "$out/diff.txt"; then echo "hidden: 0 mismatches"; else cat "$out/diff.txt"; echo "hidden: mismatches"; exit 1; fi
