FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements-runtime.txt .
COPY requirements-embeddings.txt .
RUN pip install --no-cache-dir -r requirements-runtime.txt
ARG INSTALL_SEMANTIC_EMBEDDINGS=0
RUN if [ "$INSTALL_SEMANTIC_EMBEDDINGS" = "1" ]; then \
        pip install --no-cache-dir -r requirements-embeddings.txt; \
    fi
COPY alembic.ini .
COPY alembic ./alembic
COPY configs ./configs
COPY src ./src

RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
