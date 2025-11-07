#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"

alloc() {
  local request_id=$1
  local token_count=$2
  echo "POST /alloc ${request_id} tokens=${token_count}"
  curl -sS -X POST "${BASE_URL}/alloc" \
    -H "Content-Type: application/json" \
    -d "{\"request_id\":\"${request_id}\",\"token_count\":${token_count}}"
  echo
}

free_req() {
  local request_id=$1
  echo "POST /free ${request_id}"
  curl -sS -X POST "${BASE_URL}/free" \
    -H "Content-Type: application/json" \
    -d "{\"request_id\":\"${request_id}\"}"
  echo
}

alloc "req-1" 80
alloc "req-2" 120
free_req "req-1"
alloc "req-3" 200
free_req "req-2"
alloc "req-4" 300
free_req "req-3"
alloc "req-5" 250
free_req "req-4"
free_req "req-5"
