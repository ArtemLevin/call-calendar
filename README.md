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
