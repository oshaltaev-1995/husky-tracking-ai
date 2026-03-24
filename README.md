# husky-tracking-ai

Starter architecture for the Husky Tracking web app.

## Stack
- Frontend: Angular
- Backend: FastAPI
- Database: PostgreSQL
- Migrations: Alembic
- Containers: Docker Compose

## Project structure
```text
husky-tracking-ai/
  backend/       # FastAPI app
  frontend/      # Angular app (CLI-generated)
  data/          # raw Excel files and exports
  docs/          # notes, ADRs, diagrams
  scripts/       # local helper scripts
```

## First start
1. Copy `.env.example` to `.env`
2. Copy `backend/.env.example` to `backend/.env`
3. Start Docker:
   ```bash
   docker compose up --build
   ```
4. Backend docs:
   - Swagger UI: `http://localhost:8000/docs`
5. Frontend dev server:
   - `http://localhost:4200`

## Angular bootstrap
Inside `frontend/` generate the real Angular app with Angular CLI:
```bash
npm install -g @angular/cli
ng new husky-tracking-frontend --routing --style=scss
```
Then move the generated files into `frontend/` or generate directly there.

## Database migration
From `backend/`:
```bash
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```
