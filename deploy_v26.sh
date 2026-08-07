#!/bin/bash
set -e
cd /root/docker/recipe-app

cp .env /tmp/saved_env

cp /root/docker/recipe-app/recipe-app_v26.tar.gz /tmp/recipe-app.tar.gz
tar xzf /tmp/recipe-app.tar.gz --exclude=.env

cp /tmp/saved_env .env

docker compose -f docker-compose.yml up -d --build --force-recreate backend

sleep 15

echo "=== Running seed ==="
docker exec recipe-app-backend-1 python3 /app/backend/scripts/seed_demo.py

echo "=== Health ==="
curl -s http://localhost:8456/health
echo ""

echo "=== Recipe count ==="
TOKEN=$(curl -s http://localhost:3000/auth/login -X POST -H 'Content-Type: application/json' -d '{"email":"guest@wiskfful.app","password":"guest123!"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')
curl -s "http://localhost:3000/recipes/?limit=100" -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); recipes = d if isinstance(d, list) else d.get('items', d); print(f'Recipes: {len(recipes)}')"

echo "=== Deploy done ==="
