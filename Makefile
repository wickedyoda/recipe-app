.PHONY: lint test security-check pre-commit-install docker-build docker-push

lint:
	cd backend && ruff check .

test:
	cd backend && pytest -q

security-check: lint test
	cd backend && pip install -r requirements.txt
	cd backend && bandit -q -r . || true
	cd backend && pip-audit --fix || true

pre-commit-install:
	pip install pre-commit
	pre-commit install

docker-build:
	docker compose build

docker-push:
	docker compose push
