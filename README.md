# Recipe App

Self-hosted recipe/media app with:
- User auth (`admin` / `user` roles)
- Per-user profiles
- Media ingest from TikTok, YouTube, Facebook Reels
- Audio/subtitle extraction via `yt-dlp` + `ffmpeg`
- MySQL persistence
- Mobile-first web UI

## Quick start

```bash
cp .env.example .env
# set MYSQL_ROOT_PASSWORD, MYSQL_PASSWORD, SECRET_KEY
docker compose up --build
```

Open:
- Frontend: http://localhost:3000
- API: http://localhost:8000

## Env

- `DATABASE_URL` - default MySQL in compose
- `SECRET_KEY` - JWT secret
- `MEDIA_ROOT` - media storage path
