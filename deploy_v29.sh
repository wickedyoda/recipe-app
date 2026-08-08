#!/bin/bash
set -e
cd /root/docker/recipe-app

cp .env /tmp/saved_env

cp /root/docker/recipe-app/recipe-app_v29.tar.gz /tmp/recipe-app.tar.gz
tar xzf /tmp/recipe-app.tar.gz --exclude=.env

cp /tmp/saved_env .env

docker compose -f docker-compose.yml up -d --build --force-recreate frontend

sleep 10

echo "=== Health ==="
curl -s http://localhost:8456/health
echo ""

echo "=== CSS file check ==="
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/src/style.css
echo " (style.css)"

echo "=== Logo check ==="
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/src/icons/logo-lg.png
echo " (logo-lg)"

echo "=== Done ==="