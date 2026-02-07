FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ---- system deps + sudo ----
RUN apt-get update \
 && apt-get install -y \
    python3-venv \
    alsa-utils \
    libasound2 \
    libpulse0 \
    procps \
    sudo \
    git \
 && rm -rf /var/lib/apt/lists/*

# ---- create appuser ----
RUN groupadd -g 1000 appuser \
 && useradd -u 1000 -g 1000 -m -s /bin/bash appuser

# ---- sudo for appuser ----
RUN usermod -aG sudo appuser \
 && echo "appuser ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/appuser \
 && chmod 0440 /etc/sudoers.d/appuser

# ---- pulseaudio config ----
RUN echo "default-server = tcp:host.docker.internal:4713" > /etc/pulse/client.conf

WORKDIR /app


# ---- app code ----
COPY . .
RUN chown -R appuser:appuser /app

USER appuser
