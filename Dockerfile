FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY static ./static
# The pinned official MCP server is installed into the image with the app.
RUN pip install --no-cache-dir .

ENV PORT=8080
ENV SLATESAFE_ROOT=/app
CMD exec uvicorn slatesafe.app:app --host 0.0.0.0 --port "${PORT}"
