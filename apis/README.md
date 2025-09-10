# FastAPI Backend APIs Docker Image

This runbook provides step-by-step instructions to build FastAPI Backend APIs Docker image using the provided Dockerfile.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- [Docker](https://docs.docker.com/get-docker/)

## Steps to Containerize FastAPI Backend APIs application with Docker

### 1. Review the `Dockerfile`
Ensure the `Dockerfile` is properly configured. It should:
- Use a lightweight base image (e.g., `python:3.11-slim`).
- Copy the application code into the image.
- Install only the required dependencies from `requirements.txt`.
- Set default environment variables application configuration.
- Define a `CMD` to run the FastAPI application.

### 2. Build the FastAPI Backend APIs Docker Image

Run the following command to build the FastAPI Backend APIs Docker image.
- Always tag your FastAPI Backend APIs Docker image with a semantic version (e.g., 1.0.0) instead of or in addition to the `latest` tag.

```bash
docker build -t fastapi-backend-apis:1.0.0 apis/
```

- The `-t` flag tags the image with a name (`fastapi-backend-apis:1.0.0`).
- The `apis/` specifies the directory as the build context where the `Dockerfile` resides.

To rebuild a FastAPI Backend APIs Docker image without using the cache, you can use the `--no-cache` flag with the docker build command.

```bash
docker build --no-cache --platform linux/amd64,linux/arm64 -t fastapi-backend-apis:1.0.0 apis/
```

This forces Docker to ignore any cached layers during the build process. Ensures that all steps in the Dockerfile are executed fresh, from scratch. It can be helpful when you modify the code and you're unsure whether changes in a layer are reflected, this flag ensures everything gets rebuilt.

### 3. Verify the FastAPI Backend APIs Image

After the build completes, verify that the FastAPI Backend APIs image was created successfully:

```bash
docker images
```

Look for the image `fastapi-backend-apis:1.0.0` in the list of images.

### 4. Troubleshooting the FastAPI Backend APIs Container

If your FastAPI Backend APIs container isn't behaving as expected, do the following troubleshooting steps:

1. **View FastAPI Backend APIs Container Logs**

The logs can provide information about why the Kafka FastAPI Backend APIs container stopped or what went wrong.

```bash
docker logs <fastapi-backend-apis-container-id>
```

If the container has exited, this will show the last log entry, which can help identify the cause of failure.

For real-time log streaming (useful for live troubleshooting):

```bash
docker logs -f <fastapi-backend-apis-container-id>
```

2. **Access the FastAPI Backend APIs Container's Shell**

If you need to access the FastAPI Backend APIs container's environment to debug further, you can use `docker exec` command to open a shell inside the container.

```bash
docker exec -it <fastapi-backend-apis-container-id> /bin/bash
```

### 5. Push the FastAPI Backend APIs Docker Image to DockerHub

To share your Docker image, you can push it to DockerHub. Follow these steps:

1. **Log in to DockerHub**  
    Use the `docker login` command to authenticate with your DockerHub account.

    ```bash
    docker login
    ```

2. **Tag the Image for DockerHub**  
    Tag your image with your DockerHub username and repository name.

    ```bash
    docker tag fastapi-backend-apis:1.0.0 <your-dockerhub-username>/bd25_project_f4_b-fastapi-backend-apis:latest
    ```

3. **Push the Image to DockerHub**  
    Use the `docker push` command to upload the image.

    ```bash
    docker push <your-dockerhub-username>/bd25_project_f4_b-fastapi-backend-apis:latest
    ```

    Replace `<your-dockerhub-username>` with your actual DockerHub username.

4. **Verify the Image on DockerHub**  
    Visit your DockerHub repository to confirm the image has been uploaded successfully.


# API Endpoints Reference

Below is a list of available REST and WebSocket API endpoints (as defined in the `routes/` folder). Use these details to interact with the API using Hoppscotch.

---

## REST API Endpoints

| Method | Endpoint                                | Description              | Payload (if any)    |
|--------|-----------------------------------------|--------------------------|---------------------|
| GET    | `http://localhost:8000/api/taxis`       | Retrieve all taxis       | None                |
| GET    | `http://localhost:8000/api/taxi/ids`    | Retrieve all taxi ids    | None                |
| GET    | `http://localhost:8000/api/incidents`   | Retrieve all incidents   | None                |

---

## WebSocket API Endpoints

| Endpoint                                     | Description                                                    |
|----------------------------------------------|----------------------------------------------------------------|
| `ws://localhost:8000/ws/taxis`               | Main WebSocket connection for taxis                            |
| `ws://localhost:8000/ws/incidents`           | Main WebSocket connection for latest 50 incidents              |
| `ws://localhost:8000/ws/taxi_fleet_metrics`  | Main WebSocket connection to fetch taxi fleet metrics          |

---

## Analytics API Endpoints

| Method | Endpoint                                       | Description                                 | Payload (if any)                              |
|--------|------------------------------------------------|---------------------------------------------|-----------------------------------------------|
| GET    | `http://localhost:8000/api/analytics`          | Retrieve analytics for a specific taxi ID   | Taxi ID as query parameter (e.g., `?id=3015`) |
| GET    | `http://localhost:8000/api/analytics/fleet`    | Retrieve analytics for entire taxi fleet    | None                                          |

---

# API Usage Guide

Follow the steps below to access and test the REST and WebSocket APIs using the Hoppscotch web interface.

**Before testing the APIs, ensure you have deployed the project stack using Docker Compose so that all required services are running.**

---

## REST API Access

1. **Open Hoppscotch REST API Client**  
    Go to [https://hoppscotch.io/](https://hoppscotch.io/).

2. **Set Request Details**  
    - Select the HTTP method (GET, POST, PUT, DELETE) as per the taxis endpoint table above.
    - Enter the API endpoint URL (e.g., `http://localhost:8000/api/taxis`).

3. **Send Request**  
    Click the **Send** button to execute the request and view the response.

---

## WebSocket API Access

1. **Open Hoppscotch WebSocket Client**  
    Go to [https://hoppscotch.io/realtime/websocket](https://hoppscotch.io/realtime/websocket).

2. **Connect to WebSocket**  
    - Enter your WebSocket server URL (e.g., `ws://localhost:8000/ws/taxis`).
    - Click **Connect**.

3. **View Responses**  
    - Incoming messages from the server will appear in the response area.

---

## Analytics API Access

1. **Open Hoppscotch REST API Client**  
    Go to [https://hoppscotch.io/](https://hoppscotch.io/).

2. **Set Request Details**  
    - Select the HTTP method (GET, POST, PUT, DELETE) as per the taxis endpoint table above.
    - Enter the API endpoint URL (e.g., `http://localhost:8000/api/analytics`).
    - For endpoints requiring a query parameter (e.g., `http://localhost:8000/api/analytics`), ensure you include the `taxi id` as a query parameter.

3. **Send Request**  
    Click the **Send** button to execute the request and view the response.

---

## Folder Structure

```
apis/
├── Dockerfile                      # Docker image definition for FastAPI
├── README.md                       # This documentation file
├── main.py                         # FastAPI application entry point
├── requirements.txt                # Python dependencies
├── config.py                       # Application configuration settings
├── helpers.py                      # Utility functions and helpers
├── routes/                         # API route definitions
│   ├── __init__.py                # Package initialization
│   ├── rest.py                    # REST API endpoints
│   ├── websocket.py               # WebSocket endpoints
│   └── analytics.py               # Analytics API endpoints
├── schemas/                        # Pydantic data models
│   ├── __init__.py                # Package initialization
│   └── violation_alerts.py        # Violation alert data schemas
├── influxdb/                       # InfluxDB integration
│   ├── __init__.py                # Package initialization
│   ├── fetch_taxi_metrics.py      # Individual taxi metrics queries
│   └── fetch_taxi_fleet_metrics.py # Fleet-wide metrics queries
└── redis_client/                   # Redis integration
    ├── __init__.py                # Package initialization
    └── client.py                  # Redis client configuration
```

## Reference Links

- [Docker Documentation](https://docs.docker.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FastAPI WebSockets Documentation](https://fastapi.tiangolo.com/advanced/websockets/)
