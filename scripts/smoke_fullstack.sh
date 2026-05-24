#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"

cleanup() {
  docker compose down >/dev/null 2>&1 || true
}
trap cleanup EXIT

# Why: running the stack exactly as developers do in compose catches wiring
# regressions (network, migrations, static serving) that unit tests miss.
docker compose up --build -d

for attempt in $(seq 1 30); do
  if curl -fsS "$BASE_URL/health" >/dev/null; then
    break
  fi
  sleep 1
  if [[ "$attempt" -eq 30 ]]; then
    echo "Healthcheck did not become ready in time" >&2
    exit 1
  fi
done

curl -fsS "$BASE_URL/" >/dev/null
curl -fsS "$BASE_URL/web/app.js" >/dev/null

SLOT_START="2026-06-01T10:00:00"
PAYLOAD="{\"slot_start\":\"$SLOT_START\",\"customer_name\":\"Smoke User\",\"customer_email\":\"smoke@example.com\"}"

create_code=$(curl -s -o /tmp/create_response.json -w "%{http_code}" -X POST "$BASE_URL/api/bookings/" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

if [[ "$create_code" != "201" ]]; then
  echo "Create booking expected 201, got $create_code" >&2
  cat /tmp/create_response.json >&2
  exit 1
fi

conflict_code=$(curl -s -o /tmp/conflict_response.json -w "%{http_code}" -X POST "$BASE_URL/api/bookings/" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

if [[ "$conflict_code" != "409" ]]; then
  echo "Duplicate booking expected 409, got $conflict_code" >&2
  cat /tmp/conflict_response.json >&2
  exit 1
fi

upcoming_code=$(curl -s -o /tmp/upcoming_response.json -w "%{http_code}" \
  "$BASE_URL/api/bookings/upcoming?from_ts=2026-06-01T00:00:00&limit=10&offset=0")

if [[ "$upcoming_code" != "200" ]]; then
  echo "Upcoming expected 200, got $upcoming_code" >&2
  cat /tmp/upcoming_response.json >&2
  exit 1
fi

python3 - <<'PY'
import json
from pathlib import Path

items = json.loads(Path('/tmp/upcoming_response.json').read_text())
if not isinstance(items, list) or not items:
    raise SystemExit('Upcoming response must contain at least one booking')
PY

echo "Full-stack smoke passed"
