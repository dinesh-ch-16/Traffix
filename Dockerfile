FROM python:3.11-slim

# Install SUMO
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        sumo \
        sumo-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Project
COPY . .

# SUMO location inside Linux container
ENV SUMO_HOME=/usr/share/sumo

# Render supplies the port
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-10000}"]