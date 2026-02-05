FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system audio libs
RUN apt-get update && apt-get install -y \
    alsa-utils \
    libasound2 \
    libpulse0 \
    procps \
    && rm -rf /var/lib/apt/lists/*

RUN echo "default-server = tcp:host.docker.internal:4713" > /etc/pulse/client.conf

WORKDIR /app


# Install Python requirements
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . .

# Create user safely
RUN groupadd -g 1000 appuser || groupadd audio_dev \
    && useradd -u 1000 -g 1000 -m -s /bin/bash appuser \
    && chown -R appuser:1000 /app

USER appuser