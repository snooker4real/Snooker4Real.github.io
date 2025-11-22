#!/bin/bash

# Set variables
IMAGE_NAME="node-server-app"
CONTAINER_NAME="node-server-container"
HOST_PORT=3000
CONTAINER_PORT=3000

# Build the Docker image from the server directory
echo "Building Docker image: $IMAGE_NAME from ./server"
docker build -t $IMAGE_NAME ./server

# Stop and remove the existing container if it exists
if [ "$(docker ps -a -q -f name=$CONTAINER_NAME)" ]; then
    echo "Stopping and removing existing container: $CONTAINER_NAME"
    docker stop $CONTAINER_NAME
    docker rm $CONTAINER_NAME
fi

# Run the Docker container
echo "Running Docker container: $CONTAINER_NAME"
echo "Mapping host port $HOST_PORT to container port $CONTAINER_PORT"
docker run -d --name $CONTAINER_NAME -p $HOST_PORT:$CONTAINER_PORT --env-file ./server/.env.local $IMAGE_NAME

echo "Deployment complete. Access the application at http://localhost:$HOST_PORT"
