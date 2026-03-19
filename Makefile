.PHONY: setup setup-backend setup-frontend verify-backend verify-frontend verify

setup: setup-backend setup-frontend

setup-backend:
	cd backend && uv venv && uv sync

setup-frontend:
	cd frontend && bun install

verify-backend:
	cd backend && uv sync --frozen

verify-frontend:
	cd frontend && bun run build

verify: verify-backend verify-frontend
