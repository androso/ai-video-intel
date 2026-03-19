# AI Video Intelligence Platform

Barebones monorepo scaffold for a backend-first AI video processing project.

## Stack

- Backend: Python, `uv`, FastAPI, Celery, Redis, PostgreSQL, Alembic
- Frontend: Bun, React, TypeScript, Tailwind CSS, shadcn/ui foundation
- Infra: Docker Compose, GitHub Actions skeleton

## Layout

```text
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── integrations/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── workers/
│   ├── alembic/
│   ├── scripts/
│   └── tests/
├── frontend/
│   ├── public/
│   └── src/
├── .github/workflows/
└── docker-compose.yml
```

## Quickstart

```bash
make setup
```

## Notes

- `backend/app/services/` and `backend/app/workers/` are intentionally directory-only for now.
- No feature implementation code is included in this scaffold.
