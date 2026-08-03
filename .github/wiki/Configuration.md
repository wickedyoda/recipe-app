# Configuration

## Environment variables

| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy database URL | `mysql+mysqlconnector://recipes:recipes@mysql:3306/recipes` |
| `SECRET_KEY` | JWT signing key | `change-me` |
| `MEDIA_ROOT` | Media storage root | `/media` |
| `WHISPER_MODEL` | Whisper model size | `tiny` |

## Docker Compose volumes

- `mysql_data` - MySQL data volume
- `./backend:/app/backend` - live backend reload during development

## Security notes

- Always set a strong `SECRET_KEY`
- Use a strong `MYSQL_ROOT_PASSWORD` and `MYSQL_PASSWORD`
- Do not expose MySQL directly to the internet without access controls
