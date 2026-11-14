#!/bin/bash
# Install all required Python and system dependencies
echo "Installing OS system requirements..."
sudo apt-get update -y && sudo apt-get install -y python3-pip python3-venv libpq-dev curl git

echo "Installing Python dependencies..."
pip install -r backend/requirements.txt
pip install -r ai-service/requirements.txt
echo "All dependencies installed."

