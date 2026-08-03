# Development

## Setup

```bash
git clone https://github.com/wickedyoda/recipe-app.git
cd recipe-app
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

## Run backend

```bash
export DATABASE_URL="mysql+mysqlconnector://recipes:recipes@localhost:3306/recipes"
export SECRET_KEY="dev"
python run.py
```

## Frontend

The frontend is a static HTML file. During development you can open `frontend/src/index.html` directly, or serve it via any static file server.

## Tests

No automated tests are included yet. Manual verification should cover:
- registration
- login
- admin approval
- media ingest from URL
- media upload
- profile updates
- admin user listing
