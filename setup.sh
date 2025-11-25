#!/bin/bash

echo "Building Docker image..."
docker-compose build

echo "Starting container..."
docker-compose up -d

echo "Entering container..."
docker exec -it cdmo_dev bash