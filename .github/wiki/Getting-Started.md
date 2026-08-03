# Getting Started

## Prerequisites

- Docker and Docker Compose
- Git
- GitHub account with access to the repo

## Clone and run

```bash
git clone https://github.com/wickedyoda/recipe-app.git
cd recipe-app
cp .env.example .env
# edit .env and set secrets
docker compose up --build
```

## First login

1. Open http://localhost:3000
2. Register a new account
3. Ask an admin to approve the account
4. Log in with the approved account

## Default ports

- Frontend: 3000
- Backend API: 8000
- MySQL: 3306
