#!/bin/bash
set -e
cd /root/docker/recipe-app

cp .env /tmp/saved_env

cp /root/docker/recipe-app/recipe-app_v25.tar.gz /tmp/recipe-app.tar.gz
tar xzf /tmp/recipe-app.tar.gz --exclude=.env

cp /tmp/saved_env .env

docker compose -f docker-compose.yml up -d --build --force-recreate frontend backend

echo "=== Waiting for backend ==="
sleep 15

echo "=== Running seed ==="
docker exec recipe-app-backend-1 python3 /app/backend/scripts/seed_demo.py

echo "=== Health ==="
curl -s http://localhost:8456/health
echo ""

echo "=== Deploy done ==="
