# Apache Flink PyFlink Docker Image

This runbook provides step-by-step instructions to build a custom PyFlink Docker image using the provided Dockerfile.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- [Docker](https://docs.docker.com/get-docker/)

## Folder Structure

```
flink/
├── Dockerfile                      # Custom PyFlink image definition
├── README.md                       # This documentation file
├── requirements.txt                # Python dependencies for Flink jobs
├── jobs/                          # Flink job files and configuration
│   ├── main.py                    # Main Flink job entry point
│   ├── flink-conf.yaml           # Flink cluster configuration
│   ├── config/                    # Job-specific configuration files
│   │   └── ...
│   └── operators/                 # Custom Flink operators
│       └── ...
├── monitoring/                    # Monitoring configuration
│   └── prometheus.yml             # Prometheus metrics configuration
└── scripts/                      # Utility scripts
    └── submit-job.sh             # Job submission script
```

## Steps to Containerize PyFlink Application with Docker

### 1. Review the `Dockerfile`
Ensure the `Dockerfile` is properly configured. It should:
- Use the official Flink base image (e.g., `flink:1.18.1-scala_2.12-java11`).
- Install Python and PyFlink dependencies.
- Copy job files and configuration into the image.
- Install required Python packages from `requirements.txt`.
- Set appropriate environment variables for Flink configuration.

### 2. Build the PyFlink Docker Image

Run the following command to build the PyFlink Docker image.
- Always tag your PyFlink Docker image with a semantic version (e.g., 1.18.1) instead of or in addition to the `latest` tag.

```bash
docker build -t pyflink:1.18.1 flink/
```

- The `-t` flag tags the image with a name (`pyflink:1.18.1`).
- The `flink/` specifies the directory as the build context where the `Dockerfile` resides.

To rebuild a PyFlink Docker image without using the cache, you can use the `--no-cache` flag with the docker build command.

```bash
docker build --no-cache  --platform linux/amd64,linux/arm64 -t pyflink:1.18.1 flink/
```

This forces Docker to ignore any cached layers during the build process. Ensures that all steps in the Dockerfile are executed fresh, from scratch. It can be helpful when you modify the code and you're unsure whether changes in a layer are reflected, this flag ensures everything gets rebuilt.

### 3. Verify the PyFlink Image

After the build completes, verify that the PyFlink image was created successfully:

```bash
docker images
```

Look for the image `pyflink:1.18.1` in the list of images.

### 4. Troubleshooting the PyFlink Container

If your PyFlink container isn't behaving as expected, follow these troubleshooting steps:

1. **View PyFlink Container Logs**

The logs can provide information about why the PyFlink container stopped or what went wrong.

```bash
docker logs <pyflink-container-id>
```

If the container has exited, this will show the last log entry, which can help identify the cause of failure.

For real-time log streaming (useful for live troubleshooting):

```bash
docker logs -f <pyflink-container-id>
```

2. **Access the PyFlink Container's Shell**

If you need to access the PyFlink container's environment to debug further, you can use `docker exec` command to open a shell inside the container.

```bash
docker exec -it <pyflink-container-id> /bin/bash
```

### 5. Push the PyFlink Docker Image to DockerHub

To share your Docker image, you can push it to DockerHub. Follow these steps:

1. **Log in to DockerHub**  
    Use the `docker login` command to authenticate with your DockerHub account.

    ```bash
    docker login
    ```

2. **Tag the Image for DockerHub**  
    Tag your image with your DockerHub username and repository name.

    ```bash
    docker tag pyflink:1.18.1 <your-dockerhub-username>/bd25_project_f4_b-pyflink:1.18.1
    ```

3. **Push the Image to DockerHub**  
    Use the `docker push` command to upload the image.

    ```bash
    docker push <your-dockerhub-username>/bd25_project_f4_b-pyflink:1.18.1
    ```

    Replace `<your-dockerhub-username>` with your actual DockerHub username.

4. **Verify the Image on DockerHub**  
    Visit your DockerHub repository to confirm the image has been uploaded successfully.

## Flink Job Deployment

Once the image is built, you can deploy Flink jobs using Docker Compose:

```bash
# Start Flink cluster
docker-compose up flink-jobmanager flink-taskmanager

# Submit job (handled by flink-init container)
docker-compose up flink-init
```

## Monitoring

Access the Flink Web UI at [http://localhost:8081](http://localhost:8081) to monitor job status, metrics, and performance.

## Reference Links

- [Docker Documentation](https://docs.docker.com/)
- [Apache Flink Documentation](https://flink.apache.org/)
- [PyFlink Documentation](https://nightlies.apache.org/flink/flink-docs-release-1.18/docs/dev/python/overview/)
