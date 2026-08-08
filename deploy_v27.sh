#!/bin/bash
set -e
cd /root/docker/recipe-app

cp .env /tmp/saved_env

cp /root/docker/recipe-app/recipe-app_v27.tar.gz /tmp/recipe-app.tar.gz
tar xzf /tmp/recipe-app.tar.gz --exclude=.env

cp /tmp/saved_env .env

docker compose -f docker-compose.yml up -d --build --force-recreate frontend backend

echo "=== Waiting for backend ==="
sleep 15

echo "=== Running seed ==="
docker exec recipe-app-backend-1 python3 /app/backend/scripts/seed_demo.py 2>&1

echo "=== Health ==="
curl -s http://localhost:8456/health
echo ""

echo "=== Guest login enabled ==="
curl -s http://localhost:3000/settings/guest-login-enabled
echo ""

echo "=== Recipe count ==="
TOKEN=$(curl -s http://localhost:3000/auth/login -X POST -H "Content-Type: application/json" -d '{"email":"guest@whiskful.app","password":"guest123!"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')
curl -s "http://localhost:3000/recipes" -H "Authorization: Bearer $TOKEN" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(f"Recipes: {len(d)}")'

echo "=== Done ==="