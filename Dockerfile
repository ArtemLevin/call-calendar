FROM python:3.12-slim

WORKDIR /app

# Why: installing dependencies in a separate layer keeps rebuilds fast when
# only application code changes.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Why: migrations on startup guarantee schema availability before serving
# requests in a fresh container volume.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
