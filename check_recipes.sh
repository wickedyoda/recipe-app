#!/bin/bash
TOKEN=$(curl -s http://localhost:3000/auth/login -X POST -H 'Content-Type: application/json' -d '{"email":"guest@cookierue.app","password":"guest123!"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')
echo "=== Raw response ==="
curl -s "http://localhost:3000/recipes/?limit=100" -H "Authorization: Bearer $TOKEN" | head -c 500
echo ""
echo "=== Recipe count ==="
curl -s "http://localhost:3000/recipes/?limit=100" -H "Authorization: Bearer $TOKEN" | python3 -c 'import sys,json; data=json.load(sys.stdin); print(type(data)); if isinstance(data, dict): print(list(data.keys())); if "items" in data: print(f"Items: {len(data[\"items\"])}")'
