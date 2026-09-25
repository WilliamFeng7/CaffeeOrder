#!/bin/bash

# Deployment Script for CoffeeOrder
# Run this from the deploy/ directory

# 1. Create data directory if it doesn't exist
mkdir -p ../data

# 2. Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Error: Docker is not running or not accessible."
  exit 1
fi

# 3. Build and Start Services
echo "Starting deployment..."
docker compose -f docker-compose.prod.yml up -d --build

echo "Deployment complete!"
echo "Services status:"
docker compose -f docker-compose.prod.yml ps
