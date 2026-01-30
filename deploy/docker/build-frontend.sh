#!/bin/bash
set -e

echo "Building frontend assets..."
cd /home/mediacms.io/mediacms/frontend

# Check if we need to rebuild
if [ -d "dist/static" ] && [ -d "node_modules" ]; then
    echo "Frontend already built, checking for changes..."
    # In development, you can manually delete dist/ or node_modules/ to force a rebuild
    echo "To force rebuild, delete frontend/dist/ or frontend/node_modules/"
else
    # Remove node_modules to force fresh install with updated package
    echo "Cleaning node_modules..."
    rm -rf node_modules package-lock.json

    # Install dependencies
    echo "Installing frontend dependencies..."
    npm install

    # Build the frontend for production
    echo "Building production frontend..."
    npm run dist
fi

# Always copy built assets to Django static directory
echo "Copying built assets to Django static directory..."
if [ -d "dist/static" ]; then
    rsync -av --delete dist/static/ /home/mediacms.io/mediacms/static/
    echo "Frontend assets copied successfully!"
else
    echo "Error: dist/static directory not found!"
    exit 1
fi
