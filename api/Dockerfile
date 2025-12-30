# Use Ubuntu 22.04 LTS as base image
FROM ubuntu:22.04

# Environment settings
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV POETRY_VIRTUALENVS_CREATE 0

# Set working directory
WORKDIR /app/api

# Install system packages and Python 3.11
RUN apt-get update && apt-get install -y \
    apt-transport-https \
    ca-certificates \
    supervisor \
    procps \
    cron \
    python3.11 \
    python3.11-venv \
    python3.11-gdbm \
    python3.11-dev \
    wget \
    gnupg \
    unzip \
    curl && \
    rm -rf /var/lib/apt/lists/*

# Install pip for Python 3.11
RUN curl -sSL https://bootstrap.pypa.io/get-pip.py | python3.11

# Install Poetry
RUN pip install poetry

# Copy and install dependencies
COPY poetry.lock pyproject.toml /app/api/
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction \
    && rm -rf /root/.cache/pypoetry

# Copy the rest of the application
COPY . /app/api

# Copy supervisor config
COPY ./supervisor/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy and make scripts executable
COPY --chmod=755 scripts/run.sh /app/run.sh
COPY --chmod=755 scripts/celery.sh /app/celery.sh
COPY --chmod=755 scripts/create_admin.sh /app/create_admin.sh

# Run as root
USER root

# Default command
CMD ["/app/run.sh"]
