#!/bin/bash
set -euo pipefail

echo "=== Recipe App Deployment Script ==="

REPO="https://github.com/wickedyoda/recipe-app.git"
WORKDIR="/root/docker/recipe-app"
BRANCH="first_build"

# Pull latest
echo "1. Pulling latest changes..."
cd "$WORKDIR"
git fetch origin
git checkout "$BRANCH"
git pull origin "$BRANCH" --ff-only

# Build and push images locally
echo "2. Building Docker images..."
docker compose build --no-cache

# Push to GHCR
echo "3. Pushing to GHCR..."
NEXT_VERSION=$(python3 /root/.hermes/recipe-app/scripts/get_next_version.py)
echo "   Version: $NEXT_VERSION"

docker tag recipe-app-backend:latest ghcr.io/wickedyoda/recipe-app-backend:${NEXT_VERSION}
docker tag recipe-app-frontend:latest ghcr.io/wickedyoda/recipe-app-frontend:${NEXT_VERSION}
docker tag recipe-app-backend:latest ghcr.io/wickedyoda/recipe-app-backend:latest
docker tag recipe-app-frontend:latest ghcr.io/wickedyoda/recipe-app-frontend:latest
docker push ghcr.io/wickedyoda/recipe-app-backend:${NEXT_VERSION}
docker push ghcr.io/wickedyoda/recipe-app-frontend:${NEXT_VERSION}
docker push ghcr.io/wickedyoda/recipe-app-backend:latest
docker push ghcr.io/wickedyoda/recipe-app-frontend:latest

# Pull on Docker host
echo "4. Pulling images on Docker host..."
ssh -i /root/.ssh/id_ed25519_flint4 -p 122 docker@100.125.168.30 "docker pull ghcr.io/wickedyoda/recipe-app-backend:${NEXT_VERSION} && docker pull ghcr.io/wickedyoda/recipe-app-frontend:${NEXT_VERSION}"

# Deploy on Docker host
echo "5. Redeploying on Docker host..."
ssh -i /root/.ssh/id_ed25519_flint4 -p 122 docker@100.125.168.30 "cd '$WORKDIR' && docker compose pull && docker compose up -d --build --force-recreate"

# Verify
echo "6. Verifying..."
sleep 5
curl -sf http://100.125.168.30:8456/health || echo "Backend health check failed"
echo "   Deployment complete."
