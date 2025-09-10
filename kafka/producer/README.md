# Kafka Producer Docker Image

This guide provides step-by-step instructions to build a Docker image for the Kafka Producer using best practices.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- [Docker](https://docs.docker.com/get-docker/)

## Steps to Containerize Kafka Producer with Docker

### 1. Review the `Dockerfile`
Ensure the `Dockerfile` is properly configured. It should:
- Use a lightweight base image (e.g., `python:3.11-slim`).
- Install only the required dependencies from `requirements.txt`.
- Copy the necessary files (`*.py` files and `requirements.txt`) into the image.
- Set default environment variables for Kafka Producer configuration.
- Define a `CMD` to run the `producer.py` script.

### 2. Build the Kafka Producer Docker Image

Run the following command to build the Kafka Producer Docker image.
- Always tag your Kafka Producer Docker image with a semantic version (e.g., 1.0.0) instead of or in addition to the `latest` tag.

```bash
docker build -t kafka-producer:1.0.0 kafka/producer
```

- The `-t` flag tags the image with a name (`kafka-producer:1.0.0`).
- The `kafka/producer` specifies the directory as the build context where the `Dockerfile` resides.

To rebuild a Kafka Producer Docker image without using the cache, you can use the `--no-cache` flag with the docker build command.

```bash
docker build --no-cache --platform linux/amd64,linux/arm64 -t kafka-producer:1.0.0 kafka/producer
```

This forces Docker to ignore any cached layers during the build process. Ensures that all steps in the Dockerfile are executed fresh, from scratch. It can be helpful when you modify the producer code and you're unsure whether changes in a layer are reflected, this flag ensures everything gets rebuilt.

### 3. Verify the Kafka Producer Image

After the build completes, verify that the Kafka Producer image was created successfully:

```bash
docker images
```

Look for the image `kafka-producer:1.0.0` in the list of images.

### 4. Run the Kafka Producer Docker Container

Now to run your Kafka Producer container use the following command:

```bash
docker run -d --name kafka-producer -e KAFKA_BOOTSTRAP_SERVERS=localhost:9092 -e TOPIC=taxi.raw_data.stream kafka-producer:1.0.0
```

- The `-d` flag runs the container in detached mode.
- The `--name` flag assigns the name `kafka-producer` to your container.
- The `-e` flags set environment variables for Kafka configuration.
- `kafka-producer:1.0.0` is the image tag you are running

### 5. Check if the Kafka Producer Container is Running

To check the status of your running Kafka Producer container, use:

```bash
docker ps
```

This lists all currently running containers. If you want to check all containers, including those that have exited, use:

```bash
docker ps -a
```

- `docker ps` shows only running containers.
- `docker ps -a` shows all containers, including stopped or exited ones.

### 6. Troubleshooting the Kafka Producer Container

If your Kafka Producer container isn't behaving as expected, do the following troubleshooting steps:

#### 1. View Kafka Producer Container Logs

The logs can provide information about why the Kafka Producer container stopped or what went wrong.

```bash
docker logs <kafka-producer-container-id>
```

If the container has exited, this will show the last log entry, which can help identify the cause of failure.

For real-time log streaming (useful for live troubleshooting):

```bash
docker logs -f <kafka-producer-container-id>
```

#### 2. Access the Kafka Producer Container's Shell

If you need to access the Kafka Producer container's environment to debug further, you can use `docker exec` command to open a shell inside the container.

```bash
docker exec -it <kafka-producer-container-id> /bin/bash
```

### 7. Steps to Push the Kafka Producer Image Image to a Docker Hub

#### 1. Log in to Docker Hub

Log in to your Docker Hub account using the following command:

```bash
docker login
```

Enter your Docker Hub username and password when prompted.

#### 2. Tag the Kafka Producer Image

Tag the Kafka Producer image with your Docker Hub username and repository name.

```bash
```bash
docker tag kafka-producer:1.0.0 <your-dockerhub-username>/bd25_project_f4_b-kafka-producer:latest
```

Replace `your-dockerhub-username` with your Docker Hub username.

#### 3. Push the Kafka Producer Image to Docker Hub

Push the tagged Kafka Producer image to Docker Hub:

```bash
docker push <your-dockerhub-username>/bd25_project_f4_b-kafka-producer:latest
```

This will upload the Kafka Producer image to your Docker Hub repository. Visit your Docker Hub account and verify that the image appears in your repository.

## Other Useful Docker Commands

##### Stop the Kafka Producer container:

```bash
docker stop <kafka-producer-container-id>
```

##### Remove the Kafka Producer container:

```bash
docker rm <kafka-producer-container-id>
```

##### Force remove a running Kafka Producer container:

```bash
docker rm -f <kafka-producer-container-id>
```

##### Remove Kafka Producer image:

```bash
docker rmi kafka-producer:1.0.0
```

##### Remove all stopped containers:

```bash
docker container prune
```

##### Remove all unused images:

```bash
docker image prune
```

##### Remove all unused Docker resources (containers, images, volumes, networks):

```bash
docker system prune
```

## Folder Structure

The following is the folder structure for the Kafka Producer:

```
kafka/producer/
├── .dockerignore                       # Docker ignore file for build context
├── Dockerfile                          # Docker image definition for Kafka producer
├── README.md                           # This documentation file
├── requirements.txt                    # Python dependencies
├── producer.py                         # Main Kafka producer application entry point
└── datareader.py                       # Data reading and processing utilities
```

### Data Flow
1. **Data Reading**: `datareader.py` loads and processes taxi data from source files
2. **Message Production**: `producer.py` formats data and publishes messages to Kafka topics
3. **Error Handling**: Comprehensive logging and error handling throughout the pipeline
4. **Configuration**: Environment-based configuration for different deployment scenarios

## Best Practices

- Use a lightweight base image to reduce the image size.
- Avoid copying unnecessary files into the image by using a .dockerignore file.
- Use pinned versions in requirements.txt to ensure consistent builds.
- Test the image locally before pushing it to a registry.

## Troubleshooting

- If the build fails, check the Dockerfile for errors.
- Ensure Docker is running and you have sufficient permissions to build images.
- Verify that the Kafka broker is reachable when running the container.

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [AIOKafkaProducer Client Documentation](https://aiokafka.readthedocs.io/en/stable/api.html#aiokafka.AIOKafkaProducer)
