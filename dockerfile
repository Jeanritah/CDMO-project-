# Use a lightweight Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /CDMO-PROJECT-

# Copy requirements file and install dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . /CDMO-PROJECT-

# Expose port (change this if your app runs on a different one)
EXPOSE 8000