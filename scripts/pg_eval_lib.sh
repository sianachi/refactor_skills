#!/usr/bin/env bash
# Shared helpers for optimize evals: a throwaway database in the optimize-pg container and per-request measurements.
# Requires: docker container optimize-pg (postgres:17 with pg_stat_statements preloaded) on 127.0.0.1:55432.
PG_CONTAINER=${PG_CONTAINER:-optimize-pg}
PG_URL_BASE=${PG_URL_BASE:-postgres://postgres:pg@127.0.0.1:55432}

psql_q() { docker exec -i "$PG_CONTAINER" psql -U postgres -d "$1" -v ON_ERROR_STOP=1 -tAq -c "$2"; }
psql_file() { docker exec -i "$PG_CONTAINER" psql -U postgres -d "$1" -v ON_ERROR_STOP=1 -q < "$2" >/dev/null; }
create_db() { psql_q postgres "DROP DATABASE IF EXISTS $1 WITH (FORCE)" >/dev/null 2>&1; psql_q postgres "CREATE DATABASE $1" >/dev/null; }
drop_db() { psql_q postgres "DROP DATABASE IF EXISTS $1 WITH (FORCE)" >/dev/null 2>&1 || true; }
db_url() { echo "$PG_URL_BASE/$1?sslmode=disable"; }
pgss() { # db column-expression -> sum over statements run in that database
  psql_q postgres "SELECT COALESCE(SUM($2),0) FROM pg_stat_statements WHERE dbid = (SELECT oid FROM pg_database WHERE datname = '$1')"
}
wait_http() { for _ in $(seq 120); do curl -s -o /dev/null "$1" && return 0; sleep 0.25; done; echo "server did not start: $1" >&2; return 1; }

# measure <label> <url> <pid> <db> [curl args...] -> "label|status|sha256|bytes|rss_delta_kb|queries|blocks"
measure() {
  local label=$1 url=$2 pid=$3 db=$4; shift 4
  local out; out=$(mktemp); local rssf; rssf=$(mktemp)
  local q0 b0; q0=$(pgss "$db" calls); b0=$(pgss "$db" "shared_blks_hit + shared_blks_read")
  local base; base=$(ps -o rss= -p "$pid" | tr -d ' ')
  ( peak=$base; while kill -0 "$pid" 2>/dev/null && [ ! -e "$rssf.stop" ]; do r=$(ps -o rss= -p "$pid" | tr -d ' '); [ -n "$r" ] && [ "$r" -gt "$peak" ] && peak=$r; echo "$peak" > "$rssf"; sleep 0.02; done ) &
  local sampler=$!
  local code; code=$(curl -s -o "$out" -w '%{http_code}' "$@" "$url")
  touch "$rssf.stop"; wait "$sampler" 2>/dev/null
  local peak; peak=$(cat "$rssf" 2>/dev/null || echo "$base")
  local q1 b1; q1=$(pgss "$db" calls); b1=$(pgss "$db" "shared_blks_hit + shared_blks_read")
  echo "$label|$code|$(shasum -a 256 < "$out" | cut -c1-16)|$(wc -c < "$out" | tr -d ' ')|$((peak - base))|$((q1 - q0))|$((b1 - b0))"
  rm -f "$out" "$rssf" "$rssf.stop"
}
