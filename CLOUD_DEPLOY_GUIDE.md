# Guia para publicar la app 24/7

Esta app tiene tres partes:

1. **Frontend**: Vue + Vite. Es la pantalla que usan los usuarios.
2. **Backend**: FastAPI. Es la API que recibe y guarda datos.
3. **Base de datos**: PostgreSQL. Guarda materiales, conteos y reportes.

Para que funcione 24/7 sin tu laptop, cada parte vive en la nube.

## 1. Que cambio hicimos

Antes:

- Backend usaba SQLite local.
- La base vivia en un archivo dentro de Docker/laptop.

Ahora:

- Backend usa `DATABASE_URL`.
- Si `DATABASE_URL` apunta a PostgreSQL, usa PostgreSQL.
- Localmente `docker compose up --build` levanta PostgreSQL.
- En la nube puedes usar Render Postgres, Supabase, Neon o Railway.

## 2. Probar local con PostgreSQL

```bash
docker compose down
docker compose up --build
```

URLs locales:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

Si todo esta bien, `/health` debe decir `PostgreSQL`.

## 3. Subir el codigo a GitHub

1. Crea una cuenta en GitHub.
2. Crea un repositorio nuevo.
3. Desde esta carpeta sube el proyecto:

```bash
git add .
git commit -m "Prepare cloud deployment with PostgreSQL"
git branch -M main
git remote add origin TU_URL_DE_GITHUB
git push -u origin main
```

## 4. Crear base de datos PostgreSQL

Opcion recomendada: Render Postgres o Supabase Postgres.

Guarda la connection string. Se ve parecida a:

```text
postgresql://usuario:password@host:5432/database
```

Ese valor sera tu `DATABASE_URL`.

## 5. Deploy del backend en Render

En Render:

1. New > Web Service.
2. Conecta tu repositorio de GitHub.
3. Root Directory: `backend`
4. Runtime: Python
5. Build Command:

```bash
pip install -r requirements.txt
```

6. Start Command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

7. Environment Variables:

```text
DATABASE_URL=tu_connection_string_de_postgres
FRONTEND_ORIGINS=https://tu-frontend.vercel.app
```

Cuando termine, Render te dara una URL parecida a:

```text
https://tu-backend.onrender.com
```

Prueba:

```text
https://tu-backend.onrender.com/health
```

## 6. Deploy del frontend en Vercel

En Vercel:

1. Add New Project.
2. Conecta el mismo repo de GitHub.
3. Framework: Vite.
4. Root Directory: raiz del proyecto.
5. Build Command:

```bash
npm run build
```

6. Output Directory:

```text
dist
```

7. Environment Variable:

```text
VITE_API_URL=https://tu-backend.onrender.com/api
```

Importante: despues de cambiar variables de entorno, haz redeploy.

## 7. Conceptos clave

### Frontend

El frontend no guarda datos. Solo llama a la API usando:

```text
VITE_API_URL
```

### Backend

El backend guarda datos. Se conecta a la base usando:

```text
DATABASE_URL
```

### CORS

El backend solo acepta llamadas del frontend listado en:

```text
FRONTEND_ORIGINS
```

Si tu frontend cambia de URL, actualiza esa variable.

### PostgreSQL

PostgreSQL permite varios usuarios al mismo tiempo y funciona mejor para produccion que SQLite.

## 8. Orden correcto de publicacion

1. Crear PostgreSQL.
2. Publicar backend con `DATABASE_URL`.
3. Probar `/health`.
4. Publicar frontend con `VITE_API_URL`.
5. Copiar URL de frontend en `FRONTEND_ORIGINS` del backend.
6. Redeploy backend.
7. Probar la app completa.

## 9. Recomendaciones para produccion

- Usa plan pago para base de datos si necesitas 24/7 real.
- Activa backups automaticos.
- No subas contrasenas reales a GitHub.
- Usa variables de entorno para secretos.
- Mas adelante conviene agregar login real por usuario.
