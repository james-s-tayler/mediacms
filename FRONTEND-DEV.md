# Frontend Development Guide

This guide explains how to make frontend changes and see them reflected in the Django server running on `http://127.0.0.1:8080/`.

## Quick Start

1. **Start the development environment:**
   ```bash
   docker compose -f docker-compose-dev.yaml up web -d
   ```
   
   The application will be available at `http://127.0.0.1:8080/`

2. **Make changes to the frontend:**
   - Edit files in `frontend/src/` directory
   - Example: `frontend/src/static/js/pages/HomePage.tsx`

3. **Rebuild and deploy your changes:**
   ```bash
   ./rebuild-frontend.sh
   ```
   
   This will:
   - Rebuild the frontend inside the Docker container
   - Copy the built assets to Django's static directory
   - Your changes will be immediately visible

## How It Works

### Architecture

- **Frontend**: React application in `frontend/` directory
- **Build Output**: `frontend/dist/static/` (created during build)
- **Django Static**: Assets are copied to `static/` directory
- **Server**: Django serves the application on port 80 (mapped to 127.0.0.1:8080)

### First Startup

On first startup, the `web` container automatically:
1. Installs Node.js and npm
2. Installs frontend dependencies
3. Builds the frontend for production
4. Copies assets to Django's static directory
5. Starts the Django development server

Subsequent restarts will skip the build if `frontend/dist/` and `frontend/node_modules/` exist.

### Making Changes

When you edit frontend files:
1. Make your changes in `frontend/src/`
2. Run `./rebuild-frontend.sh` to rebuild and deploy
3. Refresh your browser at `http://127.0.0.1:8080/`

### Force Clean Build

To force a complete rebuild from scratch:
```bash
docker compose -f docker-compose-dev.yaml exec web bash -c "
    cd /home/mediacms.io/mediacms/frontend && 
    rm -rf dist node_modules && 
    npm install && 
    npm run dist && 
    rsync -av --delete dist/static/ /home/mediacms.io/mediacms/static/
"
```

## Port Configuration

- Django server runs on container port 80
- Mapped to `127.0.0.1:8080` on your local machine
- Access the application at: `http://127.0.0.1:8080/`

## Troubleshooting

### Container not starting
```bash
docker compose -f docker-compose-dev.yaml logs web
```

### Force rebuild
Delete `frontend/dist/` or `frontend/node_modules/` and restart:
```bash
docker compose -f docker-compose-dev.yaml restart web
```

### Check if server is running
```bash
curl -I http://127.0.0.1:8080/
```

## Files Modified

- `docker-compose-dev.yaml` - Updated to build frontend and run on port 8080
- `frontend/packages/scripts/package.json` - Added dist, templates, lib to package files
- `deploy/docker/build-frontend.sh` - Script to build and deploy frontend assets
- `rebuild-frontend.sh` - Convenience script for rebuilding after changes
