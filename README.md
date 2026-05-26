# call-calendar

## Setup

```bash
python3 -m pip install -r requirements.txt
python3 -m pip install -r requirements-dev.txt
```

## Setup via internal mirror

Use this when direct PyPI access is restricted.

```bash
export PIP_INDEX_URL="https://pypi.my-company.local/simple"
# optional fallback mirror
# export PIP_EXTRA_INDEX_URL="https://pypi.backup.local/simple"

make setup-mirror
```

You can also run full checks in a mirror-backed virtualenv:

```bash
export PIP_INDEX_URL="https://pypi.my-company.local/simple"
make test-ci-mirror
```

## Setup via local wheelhouse (offline-friendly)

### 1) Build wheelhouse (in environment with package access)

```bash
# optionally with mirror
export PIP_INDEX_URL="https://pypi.my-company.local/simple"
make build-wheelhouse
```

### 2) Install from local wheelhouse (no index access required)

```bash
make setup-wheelhouse
```

### 3) Run checks using wheelhouse-installed environment

```bash
make test-ci-wheelhouse
```

## Docker run

```bash
docker compose up --build
```

API will be available at `http://localhost:8000` and SQLite data persists in the `sqlite_data` volume.

Frontend baseline is served from the same app at `http://localhost:8000/`.
Use the browser UI to create bookings, inspect 409/422 error handling, and page through upcoming bookings.

## API contract notes (stabilized)

- Datetime inputs use ISO-8601. The service stores and operates on naive UTC datetimes.
- `GET /api/bookings/upcoming` uses current naive UTC when `from_ts` is omitted.
- `GET /api/bookings/upcoming` supports optional `status` filtering using:
  `pending`, `confirmed`, `cancelled`, `completed`.
- Meeting metadata settings endpoints:
  - `GET /api/meeting-metadata/options`
  - `GET /api/meeting-settings`
  - `PATCH /api/meeting-settings`
- Colleague contracts (stage 2/3):
  - `GET /api/colleagues?limit=<1..200>&offset=<>=0`
  - `GET /api/colleagues/{colleague_id}/availability?from_ts=...&to_ts=...`
  - availability returns `404` for unknown colleague and `422` when `to_ts <= from_ts`
  - booking creation accepts optional `colleague_id`; when omitted, backend assigns default colleague (id=1).
- Error contracts:
  - `409` and `404` return a string `detail`;
  - `422` returns FastAPI/Pydantic validation details.
- `BookingResponse` includes `id`, `slot_start`, `customer_name`, `customer_email`, `status`.
  It also includes meeting metadata: `meeting_provider`, `meeting_timezone`, `meeting_duration_minutes`.
  `created_at` is intentionally internal DB metadata and is not part of the public response contract.

## Full-stack smoke check

Run a repeatable integration smoke that validates compose startup and key user/API flows:

```bash
make smoke-fullstack
```

The smoke verifies:
- stack health (`/health`);
- frontend entrypoint and JS asset (`/`, `/web/app.js`);
- booking create success (`201`);
- duplicate-slot conflict (`409`);
- upcoming listing (`200`) with non-empty response.

Performance budgets used by smoke defaults:
- root page: 1500ms;
- create request: 2000ms;
- upcoming request: 2000ms.


## Seed fake data for manual QA

```bash
make migrate
make seed-fake-data
```

Optional flags can be passed directly to the script:

```bash
python3 scripts/seed_fake_data.py --colleagues 10 --days 30 --bookings-per-colleague 40 --seed 123
```


## Database path note

By default the app uses an absolute SQLite path resolved from the repository root (`call_calendar.db`). This avoids running the app and seeding against different DB files when commands are launched from different working directories.


## Docker-first seeding and DB checks

When running the API in Docker (`docker compose up`), seed inside the `api` service so
fake data lands in the same `/data/call_calendar.db` volume used by the running API:

```bash
make seed-fake-data-docker
```

Quickly verify what DB the container is using and how many colleagues are stored:

```bash
make docker-db-info
```
