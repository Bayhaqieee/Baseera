#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "--- Baseera System Auto-Restarter ---"

# 1. Stop ONLY the Flask App (Preserves Milvus & SearxNG Data)
echo "[1/3] Stopping Application Container..."
sudo docker-compose -f docker-compose.prod.yml stop baseera-app

# 2. Remove the old container to force a clean slate
echo "[2/3] Cleaning up old container..."
sudo docker-compose -f docker-compose.prod.yml rm -f baseera-app

# 3. Rebuild and Start
echo "[3/3] Rebuilding and Starting Application..."
# --build: Forces recompilation of python dependencies
# --no-deps: Prevents restarting the heavy database containers
sudo docker-compose -f docker-compose.prod.yml up -d --build --no-deps baseera-app

echo "--- Success! System Restarted. ---"
echo "Monitor logs with: ./monitor_system.sh"