FROM python:3.12-slim

ARG AIOS_RELEASE_COMMIT_SHA=unbound
ARG AIOS_RELEASE_CONFIGURATION_FINGERPRINT=unbound
LABEL org.opencontainers.image.revision="${AIOS_RELEASE_COMMIT_SHA}" \
      com.global-mobility-aios.release-configuration-fingerprint="${AIOS_RELEASE_CONFIGURATION_FINGERPRINT}" \
      com.global-mobility-aios.release-identity-contract="phase22.release-identity.v1"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt constraints.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt -c /app/constraints.txt

COPY . /app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=5 CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
