# Docker

## Images

Images are published to GitHub Packages automatically.

Backend:
- `ghcr.io/wickedyoda/recipe-app-backend:latest`
- `ghcr.io/wickedyoda/recipe-app-backend:<sha>`

Frontend:
- `ghcr.io/wickedyoda/recipe-app-frontend:latest`
- `ghcr.io/wickedyoda/recipe-app-frontend:<sha>`

## Build locally

```bash
docker compose build
docker compose up
```

## Production notes

- Set `restart: unless-stopped`
- Use named volumes for media storage
- Consider a reverse proxy with TLS
- Ensure `ffmpeg`, `yt-dlp`, and `whisper` are available in the runtime container
