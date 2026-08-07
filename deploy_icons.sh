#!/bin/bash
set -e
cd /root/docker/recipe-app

cp .env /tmp/saved_env

tar xzf recipe-app-icons.tar.gz
cp /tmp/saved_env .env

docker compose -f docker-compose.yml up -d --build --force-recreate frontend

echo "=== Waiting ==="
sleep 10

echo "=== Verify icons ==="
docker exec recipe-app-frontend-1 ls -la /usr/share/nginx/html/src/icons/ | head -10

echo "=== Done ==="