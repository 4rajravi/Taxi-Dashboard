# Real-Time Traffic Monitoring Dashboard UI

This document provides step-by-step instructions for running the app in development and production environments, as well as building the Docker image.

## Running the App in Development

To develop and test the application locally, follow these steps:

### 1. Prerequisites


Before you begin, ensure you have the following installed on your system:

- [Node.js](https://nodejs.org/)
- [npm](https://www.npmjs.com/)
- [Docker](https://docs.docker.com/get-docker/)


### 2. Start the Project Stack

- In the main project root folder `bd25_project_f4_b`, run the following command to start all required services (with a small dataset preferably, e.g., 1000 records):

    ```bash
    docker compose up -d
    ```

- **Important:**  
  - **Comment out the `dashboard-ui` service** in your `docker-compose.yml` file during development.
  - **Update the `kafka-producer` service depends_on value** so that it depends on the `fastapi-backends-api` service instead of `dashboard-ui` service.

- This ensures the APIs are available for the dashboard to consume.

- After development, make sure to clean up resources with:

    ```bash
    docker compose down
    ```

### 3. Run the Dashboard Locally

- Navigate to the dashboard UI directory:

    ```bash
    cd dashboard/ui
    ```

- Install dependencies once:

    ```bash
    npm install
    ```

- Start the development server:

    ```bash
    npm run dev
    ```

- Open [http://localhost:3000](http://localhost:3000) in your browser to view the dashboard.

- **Hot Reload:**  
  The Next JS app supports hot reloading, so any changes you make to the code will automatically update in the browser when you save it.

- **Debugging:**  
  Use browser DevTools (e.g., Chrome DevTools) to inspect elements, monitor network requests, and debug JavaScript during development.

---

## Running the App in Production

To deploy the dashboard in a production environment:

### 1. Build the Docker Image

1. **Review the `Dockerfile`**  
    Ensure the `Dockerfile` is properly configured. It should:

    - Use a lightweight Node.js image for building and running the dashboard UI (e.g., `node:24.1-alpine`).
    - Set the working directory (e.g., `/app`).
    - Copy only the necessary files (such as `package.json`, `package-lock.json`, and the `app` source code) into the image.
    - Install dependencies using `npm install`.
    - Build the Next.js app using `npm run build`.
    - Use multi-stage build to create a smaller production image, copying only the built output and production dependencies.
    - Set environment variables for production.
    - Expose port 3000.
    - Define a `CMD` to start the Next.js server (e.g., `npm start`).

2. **Build the Dashboard UI Docker Image**  
    Run the following command to build the Dashboard UI Docker image.
    - Always tag your Dashboard UI Docker image with a semantic version (e.g., 1.0.0) instead of or in addition to the `latest` tag.

    ```bash
    docker build -t dashboard-ui:1.0.0 dashboard/ui
    ```

    - The `-t` flag tags the image with a name (`dashboard-ui:1.0.0`).
    - The `dashboard/ui` specifies the directory as the build context where the `Dockerfile` resides.

    To rebuild a Dashboard UI Docker image without using the cache, you can use the `--no-cache` flag with the docker build command.

    ```bash
    docker build --no-cache --platform linux/amd64,linux/arm64 -t dashboard-ui:1.0.0 dashboard/ui
    ```

    This forces Docker to ignore any cached layers during the build process. Ensures that all steps in the Dockerfile are executed fresh, from scratch. It can be helpful when you modify the application code and you're unsure whether changes in a layer are reflected, this flag ensures everything gets rebuilt.

3. **Verify the Dashboard UI Image**  
    After the build completes, verify that the Dashboard UI image was created successfully:

    ```bash
    docker images
    ```

    Look for the image `dashboard-ui:1.0.0` in the list of images.

4. **Troubleshooting the Dashboard UI Container**

    1. **View Dashboard UI Container Logs**  
        The logs can provide information about why the Dashboard UI container stopped or what went wrong.

        ```bash
        docker logs <dashboard-ui-container-id>
        ```

        If the container has exited, this will show the last log entry, which can help identify the cause of failure.

        For real-time log streaming (useful for live troubleshooting):

        ```bash
        docker logs -f <dashboard-ui-container-id>
        ```
5. **Push the Dashboard UI Docker Image to DockerHub**

    To share your Docker image, you can push it to DockerHub. Follow these steps:

    1. **Log in to DockerHub**  
        Use the `docker login` command to authenticate with your DockerHub account.

        ```bash
        docker login
        ```

    2. **Tag the Image for DockerHub**  
        Tag your image with your DockerHub username and repository name.

        ```bash
        docker tag dashboard-ui:1.0.0 <your-dockerhub-username>/bd25_project_f4_b-dashboard-ui:latest
        ```

    3. **Push the Image to DockerHub**  
        Use the `docker push` command to upload the image.

        ```bash
        docker push <your-dockerhub-username>/bd25_project_f4_b-dashboard-ui:latest
        ```

        Replace `<your-dockerhub-username>` with your actual DockerHub username.

    4. **Verify the Image on DockerHub**  
        Visit your DockerHub repository to confirm the image has been uploaded successfully.

### 2. **Deploy the Stack**

- Ensure your `docker-compose.yml` includes the `dashboard-ui` service and `kafka-producer` service depends on `dashboard-ui` service.
- Start and monitor all the services and make sure everything works fine:

```bash
docker compose up -d
```

- Access the Dashboard UI at [http://localhost:3000](http://localhost:3000).

---

## Folder Structure

```
dashboard/ui/
├── Dockerfile                      # Docker image definition for production
├── README.md                       # This documentation file
├── package.json                    # Node.js dependencies and scripts
├── package-lock.json              # Locked dependency versions
├── next.config.ts                  # Next.js configuration
├── tsconfig.json                   # TypeScript configuration
├── tailwind.config.ts              # Tailwind CSS configuration
├── postcss.config.mjs              # PostCSS configuration
├── eslint.config.mjs               # ESLint configuration
├── components.json                 # shadcn/ui components configuration
├── next-env.d.ts                   # Next.js TypeScript declarations
├── app/                           # Next.js App Router pages
│   ├── layout.tsx                 # Root layout component
│   ├── page.tsx                   # Home page component
│   ├── globals.css                # Global CSS styles
│   ├── favicon.ico                # Application favicon
│   ├── home/                      # Home page specific components
│   ├── analytics/                 # Analytics page and components
│   └── incidents/                 # Incidents page and components
├── components/                    # Reusable React components
│   ├── ui/                        # shadcn/ui base components
│   ├── map/                       # Map-related components
│   ├── analytics/                 # Analytics visualization components
│   ├── fleet-analytics/           # Fleet analytics components
│   ├── fleet-stats/               # Fleet statistics components
│   └── incidents/                 # Incident management components
├── hooks/                         # Custom React hooks
│   ├── use-fetch-taxis.ts         # Hook for fetching taxi data
│   ├── use-fetch-taxi-ids.ts      # Hook for fetching taxi IDs
│   ├── use-fetch-taxi-analytics-data.ts    # Hook for taxi analytics
│   ├── use-fetch-taxi-fleet-analytics-data.ts # Hook for fleet analytics
│   ├── use-fetch-all-incidents.ts # Hook for incident data
│   ├── use-incidents-websocket.ts # WebSocket hook for incidents
│   ├── use-mobile.ts              # Mobile device detection hook
│   └── use-resize-map-*.ts        # Map resize utility hooks
├── stores/                        # Zustand state management stores
│   ├── use-taxi-data-store.ts     # Taxi data state management
│   └── use-all-taxi-ids-store.ts  # Taxi IDs state management
├── lib/                           # Utility libraries
│   └── utils.ts                   # Common utility functions
└── public/                        # Static assets
    └── ...                        # Images, icons, and other static files
```

## Useful Documentation

- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev/)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [Zustand Documentation](https://docs.pmnd.rs/zustand/getting-started/introduction)
- [shadcn/ui Documentation](https://ui.shadcn.com/docs)
- [Docker Documentation](https://docs.docker.com/)
- [Leaflet.js Documentation](https://leafletjs.com/reference.html)
- [React Leaflet Documentation](https://react-leaflet.js.org/docs/start-introduction/)