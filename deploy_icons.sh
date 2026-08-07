#!/bin/bash
set -e
cd /root/docker/recipe-app

TMP_ENV="$(mktemp)"
cp .env "$TMP_ENV"
trap 'cp "$TMP_ENV" .env; rm -f "$TMP_ENV"' EXIT
tar xzf recipe-app-icons.tar.gz --exclude=.env
cp "$TMP_ENV" .env
docker compose -f docker-compose.yml up -d --build --force-recreate frontend

echo "=== Waiting ==="
sleep 10

echo "=== Verify icons ==="
docker exec recipe-app-frontend-1 ls -la /usr/share/nginx/html/src/icons/ | head -10

echo "=== Done ==="