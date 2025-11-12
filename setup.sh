#!/bin/bash

echo "Creating virtual environment..."
python -m venv venv

echo "Activating the virtual environment..."
source venv/bin/activate

echo "Installing pipreqs..."
pip install pipreqs

echo "Generating requirements.txt..."
pip freeze > requirements.txt

echo "Building Docker image..."
docker-compose build

echo "Starting container..."
docker-compose up -d

echo "Entering container..."
docker exec -it cdmo_app bash