FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md alembic.ini ./
COPY migrations ./migrations
COPY src ./src

RUN python -m pip install . \
    && addgroup --system physicsforge \
    && adduser --system --ingroup physicsforge physicsforge \
    && chown -R physicsforge:physicsforge /app

USER physicsforge

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn math_puzzle_agent.api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
