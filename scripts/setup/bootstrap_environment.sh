#!/bin/bash
# ==============================================================================
# NexGrad Environment Bootstrap Script
# ==============================================================================

set -e
echo "=========================================================="
echo " Bootstrapping NexGrad Self-Healing Platform Environment"
echo "=========================================================="

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "[+] Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "[+] Activating virtual environment..."
source venv/bin/activate

echo "[+] Installing backend and AI service dependencies..."
pip install --upgrade pip
pip install -r backend/requirements.txt
pip install -r ai-service/requirements.txt

echo "[+] Running Django database migrations..."
cd backend
python manage.py migrate

echo "[+] Verifying system check..."
python manage.py check

echo "[✓] NexGrad environment bootstrapped successfully!"

