# Setup Instructions

This project now runs as:

- Vue + Vite frontend on port `5173`
- FastAPI backend on port `8000`
- PostgreSQL database on port `5432`, persisted by Docker volume `postgres_data`

## Docker Setup

```bash
docker compose up --build
```

URLs:

- App: http://localhost:5173
- API health: http://localhost:8000/health
- Swagger docs: http://localhost:8000/docs

## How It Works

1. User interacts with the Vue UI.
2. Vue calls API functions from `src/api.ts`.
3. API requests go to `http://localhost:8000/api`.
4. FastAPI reads and writes PostgreSQL through SQLAlchemy in `backend/app/database.py`.
5. Docker stores PostgreSQL data in the `postgres_data` volume.

## Database Tables

- `materials_gas`
- `materials_vapor`
- `reports`
- `report_differences`

## Reset Local Docker Database

```bash
docker compose down -v
docker compose up --build
```

The `-v` removes the PostgreSQL volume, so the app starts again with seed data.

## Cloud Setup

For 24/7 cloud deployment, follow `CLOUD_DEPLOY_GUIDE.md`.
