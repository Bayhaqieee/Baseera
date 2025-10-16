#!/bin/bash

echo "--- Baseera Auto-Restarter ---"

# 1. Stop ONLY the Flask Application (Preserves Milvus/Vector Store)
echo "Stopping Application Container..."
sudo docker-compose -f docker-compose.prod.yml stop baseera-app

# 2. Remove the specific container to clear cache
echo "Removing Application Container..."
sudo docker-compose -f docker-compose.prod.yml rm -f baseera-app

# 3. Rebuild and Start (Using Configured Volumes)
echo "Rebuilding and Starting Application..."
# We use --build to ensure any pip changes in Dockerfile are caught
# We use --no-deps so it doesn't try to restart linked services (Milvus)
sudo docker-compose -f docker-compose.prod.yml up -d --build --no-deps baseera-app

echo "--- Restart Complete. Vector Store is SAFE. ---"
echo "Monitor logs with: ./monitor_system.sh"