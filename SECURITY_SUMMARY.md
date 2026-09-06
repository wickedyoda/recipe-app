# Security Scan Summary

**Date:** 2026-09-06 02:54 UTC  
**Branch:** master

## Backend
- **Base image:** `python:3.13-slim-bookworm`
- **Bandit:** 0 HIGH / 0 MEDIUM / 4 LOW
  - 4 LOW findings are intentional: demo seed password (`seed_demo.py`) and subprocess usage with `# nosec` for ffmpeg/whisper/pytesseract/ffprobe.
- **pip-audit:** No known vulnerabilities
- **Ruff:** All checks passing
- **Trivy image:** 0 CRITICAL / 0 HIGH
  - zlib1g CVE-2023-45853 documented in `.trivyignore` as Debian `will_not_fix`

## Frontend
- **Base image:** `nginx:stable-alpine`
- **Trivy image:** 0 CRITICAL / 0 HIGH
- **Ruff:** All checks passing

## Tests
- **pytest:** 3 passed, 0 failed, 2 warnings (SQLAlchemy deprecation + test JWT key length)

## Optimizations Applied
- **Backend:** uvicorn `workers=2`, DB `pool_pre_ping=True`, GZipMiddleware, batch queries, model indexes
- **Frontend:** nginx static cache headers, security headers, 50MB upload limit, extended proxy timeouts

## Reports
- `security-report-20260906-0254.json` (latest)
- `security-report-20260905-0558.json` (previous)