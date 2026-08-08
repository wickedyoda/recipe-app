#!/bin/bash
set -e
cd /root/docker/recipe-app

cp /root/docker/recipe-app/recipe-app_v33.tar.gz /tmp/recipe-app.tar.gz
tar xzf /tmp/recipe-app.tar.gz

docker compose -f docker-compose.yml up -d --build --force-recreate frontend

sleep 10

echo "=== Logo ==="
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/src/icons/logo-lg.png
echo " (logo-lg)"

echo "=== Done ==="