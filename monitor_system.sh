#!/bin/bash

echo "   Baseera System Real-time Monitor"
echo "Press Ctrl+C to exit monitoring"
echo ""

# Check if container is running
if [ "$(sudo docker ps -q -f name=baseera-app)" ]; then
    echo "✅ Container 'baseera-app' is RUNNING."
    echo "--- Streaming Logs ---"
    # Tail the logs (-f means follow/realtime)
    sudo docker logs -f baseera-app
else
    echo "❌ Container 'baseera-app' is NOT running."
    echo "Printing last 50 lines of logs for debugging:"
    sudo docker logs --tail 50 baseera-app
fi