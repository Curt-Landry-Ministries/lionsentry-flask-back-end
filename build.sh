#!/bin/bash

# Initialize default values
force_reset=false

# Prune Docker resources to prevent disk space issues
docker system prune -af --volumes

# Function to kill process on specified port
kill_port() {
    pid=$(lsof -t -i tcp:"$1")
    if [ -n "$pid" ]; then
        echo "Killing process $pid on port $1"
        kill -9 $pid
    else
        echo "No process found on port $1"
    fi
}

# Function to log in to Docker Hub
docker_login() {
    echo "Logging into Docker Hub..."
    docker logout
    docker login
}

# Function to check if Docker image exists locally and pull if it does not
check_pull_image() {
    image=$1
    echo "Checking for the Docker image for $image..."
    if [[ "$(docker images -q $image 2> /dev/null)" == "" ]]; then
        echo "Image not found locally. Pulling $image..."
        docker pull $image
        if [ $? -ne 0 ]; then
            echo "Failed to pull Docker image for $image"
            exit 1
        fi
    else
        echo "Image $image found locally."
    fi
}

# Parse command-line options
while getopts 'f-:' flag; do
  case "${flag}" in
    f) force_reset=true ;;
    -) case "${OPTARG}" in
         force-reset) force_reset=true ;;
         *) break ;;
       esac ;;
    *) break ;;
  esac
done

# Kill processes on ports 5001 and 19006
kill_port 5001
kill_port 19006

# Bring down current containers
echo "Bringing down current containers..."
docker-compose down

# Clean up Docker resources to prevent disk space issues
echo "Cleaning up Docker resources..."
docker system prune -af --volumes

# Check if force reset is requested
if [ "$force_reset" = true ]; then
    echo "Performing force reset..."
    rm -f ~/.docker/config.json
    docker_login
    check_pull_image node:18.16.1
fi

# Rebuild and start containers
echo "Rebuilding and starting containers without using cache..."
echo "Building web service with no cache..."
# Building web with no cache to make sure we're not using an old node_modules
docker-compose build --no-cache

# Start up all services
echo "Starting all services..."
docker-compose up -d
