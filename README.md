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
