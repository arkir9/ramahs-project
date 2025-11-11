FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=UTC

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./
RUN python -m pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy source
COPY . .

# Default command
CMD ["python", "main.py"]

