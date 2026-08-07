#!/bin/bash
set -e
cd /root/docker/recipe-app

cp .env /tmp/saved_env

cp /root/docker/recipe-app/recipe-app_v23.tar.gz /tmp/recipe-app-gui.tar.gz
tar xzf /tmp/recipe-app-gui.tar.gz --exclude=.env

cp /tmp/saved_env .env

docker compose -f docker-compose.yml up -d --build --force-recreate frontend backend

echo "=== Waiting for backend ==="
sleep 15

echo "=== Running seed ==="
docker exec recipe-app-backend-1 python3 /app/backend/scripts/seed_demo.py

echo "=== Health ==="
curl -s http://localhost:8456/health
echo ""

echo "=== Recipe count ==="
curl -s http://localhost:3000/recipes/ -H "Authorization: Bearer $(curl -s http://localhost:3000/auth/login -X POST -H 'Content-Type: application/json' -d '{\"email\":\"guest@cookierue.app\",\"password\":\"guest123!\"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)[\"access_token\"])')" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Recipes: {len(d) if isinstance(d, list) else len(d.get(\"items\", d))}')" 2>/dev/null || echo "Check manually"

echo "=== deploy done ==="
