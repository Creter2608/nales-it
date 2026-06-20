.PHONY: dev test lint pre-commit

dev-backend:
	cd backend && poetry run uvicorn app.main:app --reload

dev-db:
	docker-compose up -d

dev: dev-db dev-backend

lint:
	pre-commit run --all-files

test-backend:
	cd backend && poetry run pytest
