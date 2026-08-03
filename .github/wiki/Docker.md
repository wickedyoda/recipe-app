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

## Runtime dependencies

- `ffmpeg`
- `yt-dlp`
- `yt-dlp` is invoked via its Python package in the backend container
- audio/subtitle extraction depends on `ffmpeg` binaries being present in the backend image

## Media storage

Use named volumes for media to preserve uploads across rebuilds:
- `mysql_data`
- `backend_media`

## Production notes

- Set `restart: unless-stopped`
- Use named volumes for media storage
- Consider a reverse proxy with TLS
- Ensure `ffmpeg` and `yt-dlp` are available in the runtime container
