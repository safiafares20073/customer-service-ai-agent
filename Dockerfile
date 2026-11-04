# syntax=docker/dockerfile:1
FROM caddy:2.10.2 AS proxy
FROM python:3.12-slim-bookworm
COPY --from=proxy /usr/bin/caddy /usr/local/bin/caddy
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_LINK_MODE=copy
WORKDIR /app
# Use verified HTTPS with the standard trust stores; Railway rejects secret mounts.
RUN pip install --no-cache-dir uv==0.12.23
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project --python /usr/local/bin/python
COPY src ./src
COPY config ./config
COPY deployment ./deployment
RUN uv sync --frozen --no-dev --python /usr/local/bin/python
# Build context permissions may be 0600 in managed workspaces. Image contents
# are public code/config only; runtime secrets never enter this directory.
RUN chmod -R a+rX /app && groupadd -g 10001 app && useradd -u 10001 -g app -M app
ENTRYPOINT ["/app/.venv/bin/python", "-m", "yemen_customer_service.hosting.launch"]
