# CookieRu

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
- Hybrid category taxonomy: Breakfast/Lunch/Dinner + subcategories
- Per-step photos and ingredient checkoff
- Dark embedded cooking mode

## GUI examples

The app is mobile-first and uses warm minimalist styling. Key screens:

- **Home / recipe list** — hybrid category pills at top, searchable recipe cards
- **Recipe detail** — metadata, step photos, ingredient checkoff, actions
- **Cooking mode** — dark kitchen-friendly UI with large step text
- **Grocery list** — full-page shareable list with copy/export actions
- **Create / edit** — form with category, subcategory, tags, servings, difficulty

*(Screenshots and further examples are available in the project wiki.)*

![Home screen](docs/screenshots/home.png)
![Recipe detail](docs/screenshots/detail.png)
![Cooking mode](docs/screenshots/cooking-mode.png)
![Grocery export](docs/screenshots/grocery-export.png)

## Disclosure

This project was developed with AI-assisted tooling. Core implementation, design decisions, and review were performed by the repository owner. AI tools were used for iteration, prototyping, and documentation.

## Quick start

```bash
cp .env.example .env
# set MYSQL_ROOT_PASSWORD, MYSQL_PASSWORD, SECRET_KEY
# optionally set BACKEND_IMAGE/FRONTEND_IMAGE to GHCR tags
docker compose up -d
```

Open:
- Frontend: http://localhost:3000
- API: http://localhost:8000

## Env

- `DATABASE_URL` - default MySQL in compose
- `SECRET_KEY` - JWT secret
- `MEDIA_ROOT` - media storage path
- `PUBLIC_URL` - public base URL for shared links
- `ALLOWED_HOSTS` - comma-separated hostnames accepted by the API (add your deployment hostname)
- `BACKEND_IMAGE` / `FRONTEND_IMAGE` - GHCR image tags
- `BACKEND_PULL_POLICY` / `FRONTEND_PULL_POLICY` - image pull behavior, e.g. `always`
- `GHCR_TOKEN` - optional PAT with `read:packages` for private images

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
