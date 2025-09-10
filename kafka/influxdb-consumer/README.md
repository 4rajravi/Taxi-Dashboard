# Kafka InfluxDB Consumer Docker Image & Verify InfluxDB Data

This runbook provides step-by-step instructions to:
- Build Kafka InfluxDB Consumer Docker image using the provided Dockerfile.
- Verify and troubleshoot data written to InfluxDB by consumer.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- [Docker](https://docs.docker.com/get-docker/)

## Steps to Containerize Kafka InfluxDB Consumer with Docker

### 1. Review the `Dockerfile`
Ensure the `Dockerfile` is properly configured. It should:
- Use a lightweight base image (e.g., `python:3.11-slim`).
- Install only the required dependencies from `requirements.txt`.
- Copy the necessary files (`*.py` files and `requirements.txt`) into the image.
- Set default environment variables for Kafka InfluxDB Consumer configuration.
- Define a `CMD` to run the `consumer.py` script.

### 2. Build the Kafka InfluxDB Consumer Docker Image

Run the following command to build the Kafka InfluxDB Consumer Docker image.
- Always tag your Kafka InfluxDB Consumer Docker image with a semantic version (e.g., 1.0.0) instead of or in addition to the `latest` tag.

```bash
docker build -t kafka-influxdb-consumer:1.0.0 kafka/influxdb-consumer
```

- The `-t` flag tags the image with a name (`kafka-influxdb-consumer:1.0.0`).
- The `kafka/influxdb-consumer` specifies the directory as the build context where the `Dockerfile` resides.

To rebuild a Kafka InfluxDB Consumer Docker image without using the cache, you can use the `--no-cache` flag with the docker build command.

```bash
docker build --no-cache --platform linux/amd64,linux/arm64 -t kafka-influxdb-consumer:1.0.0 kafka/influxdb-consumer
```

This forces Docker to ignore any cached layers during the build process. Ensures that all steps in the Dockerfile are executed fresh, from scratch. It can be helpful when you modify the InfluxDB consumer code and you're unsure whether changes in a layer are reflected, this flag ensures everything gets rebuilt.

### 3. Verify the Kafka InfluxDB Consumer Image

After the build completes, verify that the Kafka InfluxDB Consumer image was created successfully:

```bash
docker images
```

Look for the image `kafka-influxdb-consumer:1.0.0` in the list of images.

### 4. Troubleshooting the Kafka InfluxDB Consumer Container

If your Kafka InfluxDB Consumer container isn't behaving as expected, do the following troubleshooting steps:

#### 1. View Kafka InfluxDB Consumer Container Logs

The logs can provide information about why the Kafka InfluxDB Consumer container stopped or what went wrong.

```bash
docker logs <kafka-influxdb-consumer-container-id>
```

If the container has exited, this will show the last log entry, which can help identify the cause of failure.

For real-time log streaming (useful for live troubleshooting):

```bash
docker logs -f <kafka-influxdb-consumer-container-id>
```

#### 2. Access the Kafka InfluxDB Consumer Container's Shell

If you need to access the Kafka InfluxDB Consumer container's environment to debug further, you can use `docker exec` command to open a shell inside the container.

```bash
docker exec -it <kafka-influxdb-consumer-container-id> /bin/bash
```

### 5. Push the Kafka InfluxDB Consumer Docker Image to DockerHub

To share your Docker image, you can push it to DockerHub. Follow these steps:

1. **Log in to DockerHub**  
    Use the `docker login` command to authenticate with your DockerHub account.

    ```bash
    docker login
    ```

2. **Tag the Image for DockerHub**  
    Tag your image with your DockerHub username and repository name.

    ```bash
    docker tag kafka-influxdb-consumer:1.0.0 <your-dockerhub-username>/bd25_project_f4_b-kafka-influxdb-consumer:latest
    ```

3. **Push the Image to DockerHub**  
    Use the `docker push` command to upload the image.

    ```bash
    docker push <your-dockerhub-username>/bd25_project_f4_b-kafka-influxdb-consumer:latest
    ```

    Replace `<your-dockerhub-username>` with your actual DockerHub username.

4. **Verify the Image on DockerHub**  
    Visit your DockerHub repository to confirm the image has been uploaded successfully.

## Steps to Verify Data in InfluxDB

You can check the data stored in InfluxDB by connecting to the InfluxDB container and running some useful commands.

### 1. Verify Metrics from InfluxDB Web UI

To verify metrics using the InfluxDB Web UI:

1. Open your browser and navigate to [http://localhost:8086](http://localhost:8086)

2. Log in using your configured credentials.

3. Go to the **Data Explorer** section.

4. Select the appropriate **bucket** from the dropdown menu.

5. Browse the available **measurements** and fields.

6. Use the query builder to create custom queries and visualize the data.

This allows you to inspect the metrics stored in InfluxDB and verify their correctness.

### 2. Monitor Real-time Data

Use the InfluxDB Web UI Data Explorer to:
- Browse measurements and fields
- Create custom queries
- View real-time data visualization
- Monitor data ingestion rates

These commands help you inspect and verify the data written to InfluxDB by the consumer.

## Folder Structure

```
kafka/influxdb-consumer/
├── Dockerfile                           # Docker image definition for InfluxDB consumer
├── README.md                            # This documentation file
├── requirements.txt                     # Python dependencies
├── config.py                           # Configuration settings and environment variables
├── consumer.py                         # Main Kafka consumer application entry point
├── write_taxi_data_to_influxdb.py       # Handler for writing taxi data to InfluxDB
├── write_taxi_fleet_metrics_to_influxdb.py # Handler for writing fleet metrics to InfluxDB
├── write_taxi_violation_alerts_to_influxdb.py # Handler for writing violation alerts to InfluxDB
└── helpers/                             # Helper modules directory
    └── ...                             # Additional utility modules
```

### Data Flow
1. **Consumer**: Reads messages from Kafka topics (taxi processed data, fleet metrics, violation alerts)
2. **Processing**: Transforms and validates incoming data using utility functions
3. **Storage**: Writes processed data to appropriate InfluxDB measurements with proper timestamps
4. **Monitoring**: Provides logging and error handling throughout the pipeline

### InfluxDB Data Schema
- **`taxi_metrics`**: Individual taxi location points with fields like latitude, longitude, speed, average_speed, distance_km, timestamp etc.,
- **`taxi_fleet_metrics`**: Aggregated fleet statistics
- **`taxi_violation_alerts`**: Speed violations and geofence alerts

## References

- [Docker Documentation](https://docs.docker.com/)
- [AIOKafkaConsumer Client Documentation](https://aiokafka.readthedocs.io/en/stable/api.html#aiokafka.AIOKafkaConsumer)
- [InfluxDB Documentation](https://docs.influxdata.com/)
- [InfluxDB Python Client](https://github.com/influxdata/influxdb-client-python)
