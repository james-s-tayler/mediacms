#!/bin/bash
# Script to rebuild and deploy frontend changes to the Django server
# Usage: ./rebuild-frontend.sh

set -e

echo "=== MediaCMS Frontend Rebuild Script ==="
echo ""
echo "This script will:"
echo "1. Rebuild the frontend inside the Docker container"
echo "2. Copy the built assets to Django's static directory"
echo "3. Your changes will be visible on http://127.0.0.1:8080/"
echo ""

# Check if docker-compose is running
if ! docker compose -f docker-compose-dev.yaml ps | grep -q "web.*Up"; then
    echo "ERROR: The web container is not running!"
    echo "Please start it with: docker compose -f docker-compose-dev.yaml up web -d"
    exit 1
fi

echo "Rebuilding frontend..."
docker compose -f docker-compose-dev.yaml exec web bash -c "
    cd /home/mediacms.io/mediacms/frontend && 
    rm -rf dist && 
    npm run dist && 
    rsync -av --delete dist/static/ /home/mediacms.io/mediacms/static/
"

echo ""
echo "✓ Frontend rebuilt successfully!"
echo "✓ Assets copied to Django static directory"
echo ""
echo "Your changes are now live at: http://127.0.0.1:8080/"
echo ""
