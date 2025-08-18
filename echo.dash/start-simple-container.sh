#!/bin/bash
# Script to start the simplified Docker container

# Navigate to the docker-simple directory
cd "$(dirname "$0")/docker-simple" || exit

# Check if docker is available
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed or not in PATH. Please install Docker first."
    exit 1
fi

# Check if docker-compose is available (using both potential commands)
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "Starting simplified Docker container..."
echo "This will use the configuration in the docker-simple directory"
echo "You can connect to the VNC server on port 5901"

# Build and start the container
$COMPOSE_CMD up --build -d

echo "Container should be starting now."
echo "To view logs, run: $COMPOSE_CMD logs -f"
echo "To stop the container, run: $COMPOSE_CMD down"