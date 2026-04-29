# Quickstart

## Local Docker

Run the full app locally with Docker:

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:5173
- Backend health check: http://localhost:8000/health
- API docs: http://localhost:8000/docs

PostgreSQL is stored in the Docker volume `postgres_data`.

## Stack

- Frontend: Vue 3 + Vite
- Backend: Python + FastAPI
- Database: PostgreSQL local/cloud through `DATABASE_URL`
- Local deploy: Docker Compose

## Manual Development

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
npm install
npm run dev
```

The frontend reads `VITE_API_URL`; by default it uses `http://localhost:8000/api`.

## Key Files

- `src/App.vue` - Vue inventory UI
- `src/api.ts` - frontend API client
- `backend/app/main.py` - FastAPI endpoints
- `backend/app/database.py` - SQLAlchemy database setup and seed data
- `docker-compose.yml` - local deployment
- `CLOUD_DEPLOY_GUIDE.md` - step-by-step cloud deployment guide
