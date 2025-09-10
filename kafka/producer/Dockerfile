# Use slim Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the producer script
COPY *.py .

# Default environment vars
ENV KAFKA_BROKER_ADDRESS=localhost:9092 \
    KAFKA_TOPIC=taxi.raw_data.stream \
    DATASET_SIZE_LIMIT=10357 \
    DATA_REPLAY_MODE=actual \
    DATA_REPLAY_SPEED=1.0

# Run the producer
RUN mkdir -p logs
CMD ["python", "producer.py"]
