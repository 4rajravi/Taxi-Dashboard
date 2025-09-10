# Use slim Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the consumer scripts
COPY *.py .

# Default environment vars
ENV KAFKA_BOOTSTRAP_SERVERS=localhost:9092 \
    KAFKA_REDIS_CONSUMER_STARTUP_DELAY=10 \
    KAFKA_REDIS_TAXI_DATA_CONSUMER_TOPIC=taxi.processed_data.stream \
    KAFKA_REDIS_TAXI_DATA_CONSUMER_GROUP=redis_taxi_data_consumer_group \
    KAFKA_REDIS_TAXI_VIOLATION_ALERTS_CONSUMER_TOPIC=taxi.violation_alerts.stream \
    KAFKA_REDIS_TAXI_VIOLATION_ALERTS_CONSUMER_GROUP=redis_taxi_violation_alerts_consumer_group \
    KAFKA_REDIS_TAXI_FLEET_METRICS_CONSUMER_TOPIC=taxi.redis_taxi_fleet_metrics_consumer_group.stream \
    KAFKA_REDIS_TAXI_FLEET_METRICS_CONSUMER_GROUP=redis_taxi_fleet_metrics_consumer_group \
    REDIS_HOST=localhost \
    REDIS_PORT=6379 \
    REDIS_TAXI_VIOLATION_ALERTS_STREAM=taxi_violation_alerts

# Run the consumer
CMD ["python", "consumer.py"]
