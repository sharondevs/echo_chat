#!/bin/bash

# Start script for Echo Chat API
echo "Starting Echo Chat API..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "  .env file not found. Copying from env.example..."
    cp env.example .env
    echo " Please edit .env file with your configuration"
fi

# Create data directories
mkdir -p data/chroma_db data/documents data/resume

# Install dependencies if requirements.txt is newer than last install
if [ requirements.txt -nt .requirements_installed ] || [ ! -f .requirements_installed ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    touch .requirements_installed
fi

# Start the application
echo "Starting the API server..."
python main.py 