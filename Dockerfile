FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY static ./static
RUN pip install --no-cache-dir .

ENV PORT=8080
CMD exec uvicorn slatesafe.app:app --host 0.0.0.0 --port "${PORT}"
