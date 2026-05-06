# Opciones de Deploy

Esta app tiene dos formas principales de correr:

1. Local 24/7 en tu computadora o servidor con Docker.
2. Web 24/7 con Supabase + Render + Vercel.

## Opcion A: Docker Local

Usa esta opcion para correr todo en una maquina local o servidor propio.

```bash
docker compose up --build
```

URLs:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

Variables locales:

- `backend/.env` guarda tu `OLLAMA_API_KEY`.
- Docker Compose crea PostgreSQL local automaticamente.
- Docker Compose usa `PORT=8000` para el backend aunque tu `.env` tenga otro puerto.

Para reiniciar la base local desde cero:

```bash
docker compose down -v
docker compose up --build
```

## Opcion B: Web con Supabase + Render + Vercel

Usa esta opcion para publicar la app en internet.

### 1. Supabase

1. Crea un proyecto en Supabase.
2. En el panel del proyecto, abre `Connect`.
3. Copia la connection string de PostgreSQL.
4. Recomendado para Render: usa `Session pooler` si la conexion directa IPv6 no funciona.
5. Guarda ese valor para `DATABASE_URL`.

Ejemplo de forma:

```text
postgresql://postgres.xxxxx:TU_PASSWORD@aws-0-region.pooler.supabase.com:5432/postgres?sslmode=require
```

### 2. Render Backend

Render puede usar `render.yaml` desde este repo.

Config manual si lo haces desde la pantalla de Render:

- Service type: `Web Service`
- Root Directory: `backend`
- Runtime: `Python`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Variables en Render:

```text
DATABASE_URL=tu_connection_string_de_supabase
FRONTEND_ORIGINS=https://tu-app.vercel.app
OLLAMA_URL=https://ollama.com/api/generate
OLLAMA_MODEL=gpt-oss:120b
OLLAMA_API_KEY=tu_ollama_api_key
```

Prueba Render:

```text
https://tu-backend.onrender.com/health
```

Debe responder `status: ok`.

### 3. Vercel Frontend

Vercel puede usar `vercel.json` desde este repo.

Config manual:

- Framework: `Vite`
- Build Command: `npm run build`
- Output Directory: `dist`

Variable en Vercel:

```text
VITE_API_URL=https://tu-backend.onrender.com/api
```

Despues de tener la URL final de Vercel, vuelve a Render y actualiza:

```text
FRONTEND_ORIGINS=https://tu-app.vercel.app
```

Luego redeploy del backend.

## Orden recomendado

1. Supabase: crear DB y copiar `DATABASE_URL`.
2. Render: publicar backend con `DATABASE_URL` y `OLLAMA_API_KEY`.
3. Probar `/health`.
4. Vercel: publicar frontend con `VITE_API_URL`.
5. Render: actualizar `FRONTEND_ORIGINS` con la URL de Vercel.
6. Probar la app completa.

## Archivos de soporte

- `docker-compose.yml`: deploy local con Docker.
- `render.yaml`: deploy backend en Render.
- `vercel.json`: deploy frontend en Vercel.
- `backend/.env.example`: variables del backend.
- `.env.example`: variables del frontend.
