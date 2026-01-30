#!/bin/bash
set -e

echo "Building frontend assets..."
cd /home/mediacms.io/mediacms/frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Build the frontend for production
echo "Building production frontend..."
npm run dist

# Copy built assets to Django static directory
echo "Copying built assets to Django static directory..."
if [ -d "dist/static" ]; then
    rsync -av --delete dist/static/ /home/mediacms.io/mediacms/static/
    echo "Frontend assets copied successfully!"
else
    echo "Error: dist/static directory not found!"
    exit 1
fi
