#!/bin/bash
echo "=== Health ==="
curl -s http://localhost:8456/health
echo ""
echo "=== Frontend nginx ==="
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/
echo ""
echo "=== Guest login enabled ==="
curl -s http://localhost:3000/settings/guest-login-enabled
echo ""
echo "=== Icon check ==="
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/src/icons/logo-lg.png
echo " (logo-lg)"
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/src/icons/favicon-32x32.png
echo " (favicon-32)"
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/src/icons/apple-touch-icon.png
echo " (apple-touch)"
echo "=== Done ==="