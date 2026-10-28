#!/usr/bin/env bash
# Hidden contract: run the CLI on each recorded input and compare stdout, exit code and stderr.
# Usage: check.sh <binary> [record]  (record rewrites expected.txt from <binary>)
set -u
dir=$(dirname "$0"); bin=$1; fails=0
cases=("c2f 100" "f2c 32" "c2f -40" "f2c 98.6" "c2f 0.005" "f2c -459.67" "c2f -459.68" "c2f abc" "k2c 10" "c2f" "c2f 1 2" "c2f 1e3" "f2c NaN" "k2c -500" "k2c abc" "")
[ "${2:-}" = record ] && : > "$dir/expected.txt"
for args in "${cases[@]}"; do
  out=$("$bin" $args 2>/tmp/hc_err); code=$?
  line="$args|$out|$code|$(cat /tmp/hc_err)"
  if [ "${2:-}" = record ]; then echo "$line" >> "$dir/expected.txt"
  elif ! grep -qxF -- "$line" "$dir/expected.txt"; then echo "MISMATCH: $line"; fails=$((fails+1)); fi
done
rm -f /tmp/hc_err
[ "${2:-}" = record ] || echo "hidden: $fails mismatches"
[ $fails -eq 0 ]
