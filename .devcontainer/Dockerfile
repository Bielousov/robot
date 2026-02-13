FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=America/Vancouver
ENV DEBIAN_FRONTEND=noninteractive

# ---- system deps + sudo + tzdata ----
RUN apt-get update \
 && apt-get install -y \
    alsa-utils \
    git \
    libatomic1 \
    python3-venv \
    sudo \
    wget \
    tzdata \
    unzip \
    zstd \
 && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
 && echo $TZ > /etc/timezone \
 && rm -rf /var/lib/apt/lists/*

# ---- create appuser ----
RUN groupadd -g 1000 appuser \
 && useradd -u 1000 -g 1000 -m -s /bin/bash appuser

# ---- sudo for appuser ----
RUN usermod -aG sudo appuser \
 && echo "appuser ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/appuser \
 && chmod 0440 /etc/sudoers.d/appuser

WORKDIR /app

# ---- app code ----
COPY . .
RUN chown -R appuser:appuser /app
USER appuser
