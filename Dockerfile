FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY static ./static
# The live ClickHouse gateway launches the official MCP server with `uv run`.
RUN pip install --no-cache-dir . uv

ENV PORT=8080
ENV SLATESAFE_ROOT=/app
CMD exec uvicorn slatesafe.app:app --host 0.0.0.0 --port "${PORT}"
