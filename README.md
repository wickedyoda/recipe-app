# Recipe App

Self-hosted recipe/media app with:
- User auth (`admin` / `user` roles)
- Per-user profiles
- Admin approval flow for new accounts
- Media ingest from TikTok, YouTube, Facebook Reels
- File upload support
- Audio/subtitle extraction via `yt-dlp` + `ffmpeg`
- MySQL persistence
- Mobile-first web UI
- Docker Compose deployment
- Recipe photos, categories, favorites, print view, scaling
- Grocery list sharing via link, SMS, email, and text copy

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
- `PUBLIC_URL` - public base URL for shared links

## CI / security

CI runs on pull requests via GitHub Actions:
- Python Lint
- Python Tests
- Python SAST & Dependencies
- Secrets & Container Scan
- YAML & Compose Validate
- Frontend Validate

## Wiki

See the project [Wiki](https://github.com/wickedyoda/recipe-app/wiki) for setup guides, API docs, and development notes.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

This project is licensed under the **MIT License** with attribution requirement.

Original tooling and concepts are based on the excellent open-source video extraction ecosystem:
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) (yt-dlp org contributors)
- [FFmpeg](https://ffmpeg.org/) (FFmpeg contributors)
- [OpenAI Whisper](https://github.com/openai/whisper) (OpenAI)

Original authors/owners retain copyright; this implementation adds app-specific integration, user auth, storage indexing, and packaging.
