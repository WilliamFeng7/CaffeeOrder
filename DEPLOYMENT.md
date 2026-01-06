# Deployment Guide

This guide describes how to deploy the CoffeeOrder application to a Linux server (e.g., Ubuntu/Debian/CentOS).

## Prerequisites

1.  **Server**: A Linux server with public IP access.
2.  **Docker**: docker and docker compose plugin installed.
    -   [Install Docker on Ubuntu](https://docs.docker.com/engine/install/ubuntu/)
    -   [Install Docker on Debian](https://docs.docker.com/engine/install/debian/)
    -   [Install Docker on CentOS](https://docs.docker.com/engine/install/centos/)

## Quick Start
1.  **Clone/Upload Code**: Upload the entire project directory to your server (e.g., using `scp` or `git clone`).
2.  **Run Deployment Script**:
    ```bash
    cd CoffeeOrder
    chmod +x deploy.sh
    ./deploy.sh
    ```
3.  **Access Config**:
    -   **Student App**: `http://<YOUR_SERVER_IP>`
    -   **Admin Panel**: `http://<YOUR_SERVER_IP>:8080`
    -   **Barista KDS**: `http://<YOUR_SERVER_IP>:8081`

## Manual Deployment
If you prefer to run commands manually:

1.  Create the data directory for the database:
    ```bash
    mkdir -p data
    ```
2.  Start the services using the production configuration:
    ```bash
    docker compose -f docker-compose.prod.yml up -d --build
    ```

## Data Persistence
-   The database is stored in the `./data/coffee.db` file on the host machine.
-   **Backup**: To backup your data, simply copy the `./data/coffee.db` file to a safe location.

## Configuration
-   **Environment Variables**: The `docker-compose.prod.yml` file sets the `DATABASE_URL` to store the database in the mounted volume.
-   **Ports**:
    -   Backend: Internal 80, Exposed 8000
    -   Student: Exposed 80
    -   Admin: Exposed 8080
    -   Barista: Exposed 8081

## Troubleshooting
-   **Check Logs**:
    ```bash
    docker compose -f docker-compose.prod.yml logs -f
    ```
-   **Restart Services**:
    ```bash
    docker compose -f docker-compose.prod.yml restart
    ```
