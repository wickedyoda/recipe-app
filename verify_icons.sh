#!/bin/bash
set -euo pipefail

check_code() {
  local url="$1"
  local label="$2"
  local code
  code="$(curl -sS -o /dev/null -w "%{http_code}" "$url")"
  echo "${code} (${label})"
  [ "$code" = "200" ]
}

echo "=== Health ==="
curl -fsS http://localhost:8456/health
echo ""

echo "=== Frontend nginx ==="
check_code "http://localhost:3000/" "frontend /"
echo ""

echo "=== Guest login enabled ==="
curl -fsS http://localhost:3000/settings/guest-login-enabled
echo ""

echo "=== Icon check ==="
check_code "http://localhost:3000/src/icons/logo-lg.png" "logo-lg"
check_code "http://localhost:3000/src/icons/favicon-32x32.png" "favicon-32"
check_code "http://localhost:3000/src/icons/apple-touch-icon.png" "apple-touch"

echo "=== Done ==="