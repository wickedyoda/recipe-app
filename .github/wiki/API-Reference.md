# API Reference

## Base URL

- Local: `http://localhost:8000`

## Authentication

All endpoints except `/auth/login`, `/auth/register`, and `/health` require a Bearer token.

```
Authorization: Bearer <access_token>
```

## Endpoints

### Auth

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `PATCH /auth/me`
- `GET /auth/users`
- `GET /auth/users/pending`
- `POST /auth/users/approve`

### Media

- `POST /media/ingest`
- `POST /media/upload`
- `GET /media/items`
- `GET /media/cookbooks`
- `POST /media/cookbooks`

### Health

- `GET /health`

## Errors

- `400` - bad request
- `401` - unauthorized
- `403` - forbidden or pending approval
- `404` - not found
