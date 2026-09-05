#!/usr/bin/env bash
#
# deploy-recipe-app.sh
# Build, tag, push, and deploy recipe-app with auto-incrementing alpha version.
# Version pattern: alpha-1.00.001, alpha-1.00.002, etc.
#
# Usage: ./scripts/deploy-recipe-app.sh
#
# Prerequisites:
# - GITHUB_TOKEN env var with repo + packages:write scopes
# - Docker login to ghcr.io
# - SSH access to docker host via ~/.ssh/id_ed25519_flint4

set -euo pipefail

REPO="wickedyoda/recipe-app"
DOCKER_HOST="100.125.168.30"
SSH_KEY="/root/.ssh/id_ed25519_flint4"
SSH_PORT="122"
BASE_VERSION="alpha-1.00"

echo "[*] Starting recipe-app deployment..."

# 0. Login to GHCR
echo "[*] Logging in to GHCR..."
echo "${GITHUB_TOKEN}" | docker login ghcr.io -u wickedyoda --password-stdin 2>&1 | tail -1

# 1. Get the last version from GHCR tags
echo "[*] Determining next version..."
LAST_TAG=$(curl -s -H "Authorization: bearer ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/${REPO}/releases?per_page=5" 2>/dev/null \
  | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for r in data:
        tag = r.get('tag_name', '')
        if tag.startswith('alpha-1.00.'):
            print(tag)
            break
    else:
        print('alpha-1.00.000')
except:
    print('alpha-1.00.000')
" 2>/dev/null || echo "alpha-1.00.000")

if [[ "$LAST_TAG" == "alpha-1.00.000" ]]; then
  NEXT_VERSION="${BASE_VERSION}.001"
else
  NUM=$(echo "$LAST_TAG" | grep -oP '\d+$')
  NEXT_VERSION="${BASE_VERSION}.$(printf '%03d' $((10#$NUM + 1)))"
fi

echo "[+] New version: $NEXT_VERSION"

# 2. Build images with --no-cache
echo "[*] Building images (no-cache)..."
docker compose build --no-cache 2>&1 | tail -3

# 3. Tag and push
echo "[*] Tagging and pushing images..."

# Frontend
docker tag recipe-app-frontend:latest "ghcr.io/${REPO}-frontend:${NEXT_VERSION}"
docker push "ghcr.io/${REPO}-frontend:${NEXT_VERSION}" 2>&1 | tail -1
docker tag recipe-app-frontend:latest "ghcr.io/${REPO}-frontend:alpha-1.0"
docker push "ghcr.io/${REPO}-frontend:alpha-1.0" 2>&1 | tail -1

# Backend
docker tag recipe-app-backend:latest "ghcr.io/${REPO}-backend:${NEXT_VERSION}"
docker push "ghcr.io/${REPO}-backend:${NEXT_VERSION}" 2>&1 | tail -1
docker tag recipe-app-backend:latest "ghcr.io/${REPO}-backend:alpha-1.0"
docker push "ghcr.io/${REPO}-backend:alpha-1.0" 2>&1 | tail -1

echo "[+] Images pushed: ${NEXT_VERSION}"

# 4. Sync Dockerfiles and compose to docker host
echo "[*] Syncing to docker host..."
scp -i "$SSH_KEY" -P "$SSH_PORT" Dockerfile.frontend Dockerfile.backend docker-compose.yml \
  "root@${DOCKER_HOST}:/root/docker/recipe-app/" 2>&1

# 5. Also sync frontend changes
scp -i "$SSH_KEY" -P "$SSH_PORT" frontend/src/index.html frontend/src/style.css \
  "root@${DOCKER_HOST}:/root/docker/recipe-app/frontend/src/" 2>&1

# 6. Deploy on docker host
echo "[*] Deploying on docker host..."
ssh -i "$SSH_KEY" -p "$SSH_PORT" "root@${DOCKER_HOST}" \
  "cd /root/docker/recipe-app && \
   docker compose down 2>&1 | tail -3 && \
   docker compose up -d 2>&1 | tail -3 && \
   sleep 10 && \
   curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/ && echo ' - frontend' && \
   curl -s -o /dev/null -w '%{http_code}' http://localhost:8456/health && echo ' - backend'"

echo "[+] Deployment complete!"
echo "[+] Version: ${NEXT_VERSION}"
echo "[+] Frontend: https://recipe.tyates.one"
echo "[+] Backend API: http://${DOCKER_HOST}:8456"
