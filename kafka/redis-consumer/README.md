# Kafka Redis Consumer Docker Image & Verify Redis Data

This runbook provides step-by-step instructions to:
- Build Kafka Redis Consumer Docker image using the provided Dockerfile.
- Verify and troubleshoot data written to Redis by consumer.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- [Docker](https://docs.docker.com/get-docker/)

## Steps to Containerize Kafka Redis Consumer with Docker

### 1. Review the `Dockerfile`
Ensure the `Dockerfile` is properly configured. It should:
- Use a lightweight base image (e.g., `python:3.11-slim`).
- Install only the required dependencies from `requirements.txt`.
- Copy the necessary files (`*.py` files and `requirements.txt`) into the image.
- Set default environment variables for Kafka Redis Consumer configuration.
- Define a `CMD` to run the `consumer.py` script.

### 2. Build the Kafka Redis Consumer Docker Image

Run the following command to build the Kafka Redis Consumer Docker image.
- Always tag your Kafka Redis Consumer Docker image with a semantic version (e.g., 1.0.0) instead of or in addition to the `latest` tag.

```bash
docker build -t kafka-redis-consumer:1.0.0 kafka/redis-consumer
```

- The `-t` flag tags the image with a name (`kafka-redis-consumer:1.0.0`).
- The `kafka/redis-consumer` specifies the directory as the build context where the `Dockerfile` resides.

To rebuild a Kafka Redis Consumer Docker image without using the cache, you can use the `--no-cache` flag with the docker build command.

```bash
docker build --no-cache --platform linux/amd64,linux/arm64 -t kafka-redis-consumer:1.0.0 kafka/redis-consumer
```

This forces Docker to ignore any cached layers during the build process. Ensures that all steps in the Dockerfile are executed fresh, from scratch. It can be helpful when you modify the redis consumer code and you're unsure whether changes in a layer are reflected, this flag ensures everything gets rebuilt.

### 3. Verify the Kafka Redis Consumer Image

After the build completes, verify that the Kafka Redis Consumer image was created successfully:

```bash
docker images
```

Look for the image `kafka-redis-consumer:1.0.0` in the list of images.

### 4. Troubleshooting the Kafka Redis Consumer Container

If your Kafka Redis Consumer container isn't behaving as expected, do the following troubleshooting steps:

#### 1. View Kafka Redis Consumer Container Logs

The logs can provide information about why the Kafka Redis Consumer container stopped or what went wrong.

```bash
docker logs <kafka-redis-consumer-container-id>
```

If the container has exited, this will show the last log entry, which can help identify the cause of failure.

For real-time log streaming (useful for live troubleshooting):

```bash
docker logs -f <kafka-redis-consumer-container-id>
```

#### 2. Access the Kafka Redis Consumer Container's Shell

If you need to access the Kafka Redis Consumer container's environment to debug further, you can use `docker exec` command to open a shell inside the container.

```bash
docker exec -it <kafka-redis-consumer-container-id> /bin/bash
```

### 5. Push the Kafka Redis Consumer Docker Image to DockerHub

To share your Docker image, you can push it to DockerHub. Follow these steps:

1. **Log in to DockerHub**  
    Use the `docker login` command to authenticate with your DockerHub account.

    ```bash
    docker login
    ```

2. **Tag the Image for DockerHub**  
    Tag your image with your DockerHub username and repository name.

    ```bash
    docker tag kafka-redis-consumer:1.0.0 <your-dockerhub-username>/bd25_project_f4_b-kafka-redis-consumer:latest
    ```

3. **Push the Image to DockerHub**  
    Use the `docker push` command to upload the image.

    ```bash
    docker push <your-dockerhub-username>/bd25_project_f4_b-kafka-redis-consumer:latest
    ```

    Replace `<your-dockerhub-username>` with your actual DockerHub username.

4. **Verify the Image on DockerHub**  
    Visit your DockerHub repository to confirm the image has been uploaded successfully.

## Steps to Verify Data in Redis

You can check the data stored in Redis by connecting to the Redis container and running some useful commands.

### 1. Exec into the Redis Container

```bash
docker exec -it redis /bin/bash
```

### 2. Open the Redis CLI

Run the below command in the container terminal to access Redis CLI.

```bash
redis-cli
```

### 3. Useful Redis Commands

- **Check Redis server status:**
    ```bash
    ping
    ```
- **List all taxi keys:**
    ```bash
    keys taxi:*
    ```
- **Count all taxi keys:**
    ```bash
    eval "return #redis.call('keys', ARGV[1])" 0 "taxi:*"
    ```
- **View all info for a specific taxi (e.g., taxi:10):**
    ```bash
    hgetall taxi:10
    ```
- **Get total memory used by all taxi keys (Redis >= 4.0):**
    ```bash
    EVAL "local sum = 0 for _,k in ipairs(redis.call('KEYS', 'taxi:*')) do sum = sum + redis.call('MEMORY', 'USAGE', k) end return sum" 0
    ```
- **Show Redis memory stats:**
    ```bash
    info memory
    ```
- **Get the number of keys in the database:**
    ```bash
    dbsize
    ```
- **Monitor live redis writes:**
    ```bash
    monitor
    ```
- **Read new entries from a Redis stream:**
    ```bash
    XREAD BLOCK 0 STREAMS taxi_violation_alerts $
    ```
- **Get the current length of a Redis stream:**
    ```bash
    XLEN taxi_violation_alerts
    ```
- **View the last 50 items in a Redis stream:**
    ```bash
    XREVRANGE taxi_violation_alerts + - COUNT 50
    ```

These commands help you inspect and verify the data written to Redis by the consumer.

## Folder Structure

```
kafka/redis-consumer/
├── Dockerfile                           # Docker image definition for Redis consumer
├── README.md                            # This documentation file
├── requirements.txt                     # Python dependencies
├── config.py                           # Configuration settings and environment variables
├── consumer.py                         # Main Kafka consumer application entry point
├── consumer_utils.py                   # Utility functions for consumer operations
├── redis_client.py                    # Redis client configuration and connection
├── write_taxi_data_to_redis.py         # Handler for writing taxi data to Redis
├── write_taxi_fleet_metrics_to_redis.py # Handler for writing fleet metrics to Redis
├── write_taxi_violation_alerts_to_redis.py # Handler for writing violation alerts to Redis
```

## File Descriptions

### Core Application
- **`consumer.py`**: Main Kafka consumer application that orchestrates data consumption and processing
- **`config.py`**: Environment variable management and application configuration settings
- **`consumer_utils.py`**: Common utility functions for Kafka consumer operations and error handling
- **`requirements.txt`**: Python package dependencies including aiokafka and redis libraries

### Redis Integration
- **`redis_client.py`**: Redis client setup, connection pooling, and configuration management
- **`write_taxi_data_to_redis.py`**: Processes and writes individual taxi location data to Redis hashes
- **`write_taxi_fleet_metrics_to_redis.py`**: Handles fleet-wide metrics data storage in Redis
- **`write_taxi_violation_alerts_to_redis.py`**: Manages violation alert data storage in Redis streams

### Support Files
- **`helpers/`**: Additional utility modules for data processing and transformation
- **`Dockerfile`**: Multi-stage Docker build configuration for production deployment

### Data Flow
1. **Consumer**: Reads messages from Kafka topics (taxi data, fleet metrics, violation alerts)
2. **Processing**: Transforms and validates incoming data using utility functions
3. **Storage**: Writes processed data to appropriate Redis data structures (hashes, streams)
4. **Monitoring**: Provides logging and error handling throughout the pipeline

## References

- [Docker Documentation](https://docs.docker.com/)
- [AIOKafkaConsumer Client Documentation](https://aiokafka.readthedocs.io/en/stable/api.html#aiokafka.AIOKafkaConsumer)
- [Redis Documentation](https://redis.io/documentation/)
