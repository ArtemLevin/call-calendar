#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
ROOT_BUDGET_MS="${ROOT_BUDGET_MS:-1500}"
CREATE_BUDGET_MS="${CREATE_BUDGET_MS:-2000}"
UPCOMING_BUDGET_MS="${UPCOMING_BUDGET_MS:-2000}"

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

root_ms=$(curl -s -o /dev/null -w "%{time_total}" "$BASE_URL/")
root_ms=$(python3 - <<PY
print(int(float("$root_ms") * 1000))
PY
)
if (( root_ms > ROOT_BUDGET_MS )); then
  echo "Root page exceeded budget: ${root_ms}ms > ${ROOT_BUDGET_MS}ms" >&2
  exit 1
fi

curl -fsS "$BASE_URL/web/app.js" >/dev/null

SMOKE_PAYLOAD_JSON="$(python3 scripts/generate_smoke_booking_payload.py)"
SLOT_START="$(python3 - <<PY
import json
print(json.loads("""$SMOKE_PAYLOAD_JSON""")["slot_start"])
PY
)"
FROM_TS="$(python3 - <<PY
import json
print(json.loads("""$SMOKE_PAYLOAD_JSON""")["from_ts"])
PY
)"
EMAIL_SUFFIX="$(python3 - <<PY
import json
print(json.loads("""$SMOKE_PAYLOAD_JSON""")["email_suffix"])
PY
)"
BUDGET_SLOT_START="$(python3 - <<PY
import json
print(json.loads("""$SMOKE_PAYLOAD_JSON""")["budget_slot_start"])
PY
)"
PAYLOAD="{\"slot_start\":\"$SLOT_START\",\"customer_name\":\"Smoke User\",\"customer_email\":\"smoke-${EMAIL_SUFFIX}@example.com\"}"

create_code=$(curl -s -o /tmp/create_response.json -w "%{http_code}" -X POST "$BASE_URL/api/bookings/" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")
create_ms=$(curl -s -o /dev/null -w "%{time_total}" -X POST "$BASE_URL/api/bookings/" \
  -H "Content-Type: application/json" \
  -d "{\"slot_start\":\"$BUDGET_SLOT_START\",\"customer_name\":\"Budget User\",\"customer_email\":\"budget-${EMAIL_SUFFIX}@example.com\"}")
create_ms=$(python3 - <<PY
print(int(float("$create_ms") * 1000))
PY
)
if (( create_ms > CREATE_BUDGET_MS )); then
  echo "Create request exceeded budget: ${create_ms}ms > ${CREATE_BUDGET_MS}ms" >&2
  exit 1
fi

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
  "$BASE_URL/api/bookings/upcoming?from_ts=$FROM_TS&limit=10&offset=0")
upcoming_ms=$(curl -s -o /dev/null -w "%{time_total}" \
  "$BASE_URL/api/bookings/upcoming?from_ts=$FROM_TS&limit=10&offset=0")
upcoming_ms=$(python3 - <<PY
print(int(float("$upcoming_ms") * 1000))
PY
)
if (( upcoming_ms > UPCOMING_BUDGET_MS )); then
  echo "Upcoming request exceeded budget: ${upcoming_ms}ms > ${UPCOMING_BUDGET_MS}ms" >&2
  exit 1
fi

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
