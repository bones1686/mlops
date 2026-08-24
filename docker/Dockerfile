FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY pyproject.toml README.md requirements.txt ./
RUN pip install -r requirements.txt

COPY src ./src
COPY data ./data
RUN pip install --no-deps .

RUN useradd --create-home --uid 10001 appuser && \
    mkdir -p /app/artifacts && chown -R appuser:appuser /app
USER appuser

CMD ["uvicorn", "support_classifier.api:app", "--host", "0.0.0.0", "--port", "8000"]
