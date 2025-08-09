# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates tar \
    && rm -rf /var/lib/apt/lists/*

ARG PIPER_URL=https://github.com/rhasspy/piper/releases/latest/download/piper_linux_x86_64.tar.gz
RUN mkdir -p /opt/piper \
    && echo "Downloading Piper from: ${PIPER_URL}" \
    && curl -L "$PIPER_URL" | tar -xz --strip-components=1 -C /opt/piper \
    && chmod +x /opt/piper/piper \
    && ls -la /opt/piper

ENV PATH="/opt/piper:${PATH}" \
    ESPEAK_DATA_PATH="/opt/piper/espeak-ng-data"

WORKDIR /app

COPY server/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY server /app
RUN mkdir -p /data/model

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
