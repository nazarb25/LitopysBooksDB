FROM ghcr.io/astral-sh/uv:0.12.17-python3.14-trixie-slim

ENV PYTHONUNBUFFERED=1 \
    LITOPYSDB_AUTO_MIGRATE=false \
    LITOPYSDB_DATABASE_READ_ONLY=true \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project

COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./
RUN uv sync --locked --no-dev --no-editable \
    && .venv/bin/litopysdb db-download \
    && .venv/bin/litopysdb db-upgrade

RUN useradd --create-home --uid 10001 litopysdb \
    && chown -R litopysdb:litopysdb /app
USER litopysdb

EXPOSE 10000

CMD ["/bin/sh", "-c", "exec .venv/bin/litopysdb serve --host 0.0.0.0 --port \"${PORT:-10000}\""]
