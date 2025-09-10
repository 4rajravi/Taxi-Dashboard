# Use slim Python base image
FROM python:3.11-slim

# Install build dependencies
RUN apt-get update && apt-get install -y gcc && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy FastAPI application code
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Default environment vars
ENV REDIS_HOST=redis \
    REDIS_PORT=6379 \
    REDIS_TAXI_VIOLATION_ALERTS_STREAM=taxi_violation_alerts \
    WEBSOCKET_INTERVAL_IN_SECONDS=1 \
    DATASET_SIZE_LIMIT=10357 \
    DATA_REPLAY_MODE=actual \
    DATA_REPLAY_SPEED=1.0 \
    INFLUXDB_URL=http://localhost:8086 \
    INFLUXDB_ORG=bd25-project-f4-b \
    INFLUXDB_BUCKET=taxi_processed_data_stream

# Run the FastAPI app with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
