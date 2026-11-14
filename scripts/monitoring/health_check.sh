#!/bin/bash
# NexGrad Service Health Probe
BACKEND_HOST=${1:-"127.0.0.1"}
AI_HOST=${2:-"127.0.0.1"}

echo "--- Checking Backend Service (Port 8000) ---"
curl -s -o /dev/null -w "%{http_code}" http://${BACKEND_HOST}:8000/healthz || echo "BACKEND DOWN"
echo ""

echo "--- Checking AI Microservice (Port 8001) ---"
curl -s -o /dev/null -w "%{http_code}" http://${AI_HOST}:8001/health || echo "AI SERVICE DOWN"
echo ""

