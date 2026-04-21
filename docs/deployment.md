# Deployment

## Current deployment model

The project is currently deployed on a VPS using Docker-based infrastructure.

The deployment consists of:

- **Frontend** served by Nginx
- **Backend** served by FastAPI / Uvicorn
- **Database** served by PostgreSQL
- **Reverse proxy routing** from frontend to backend under `/api/v1`

## Production setup

The production deployment uses:

- `docker-compose.prod.yml`
- frontend production Docker image
- backend production container
- PostgreSQL container
- Nginx configuration for frontend and API proxying

## Why this deployment approach was chosen

This approach was chosen because it is:

- simple enough for an MVP
- reproducible
- suitable for learning and demonstration
- practical for a student full-stack project
- close enough to real production workflows to be meaningful

## Production notes

The deployed environment already supports:

- application startup through Docker Compose
- database migrations through Alembic
- backup and restore workflow
- code updates through Git + rebuild
- backend running without development auto-reload

## Deployment flow

A simplified deployment workflow looks like this:

1. push code to GitHub
2. connect to the server via SSH
3. pull the latest code
4. rebuild containers
5. restart the services

## Data persistence

PostgreSQL data is persisted through Docker volumes.

This means:

- data survives container recreation
- backups can be created separately
- the application state is not tied only to a running process

## Backup workflow

A database backup workflow is already in place.

The current maintenance setup supports:

- creating SQL dumps on the server
- downloading dumps to a local machine
- restoring the database from backup when needed

## Operations guide

Deployment and maintenance commands are documented in:

- `OPERATIONS.md`

This includes:

- connecting to the server
- checking running services
- reading logs
- creating backups
- restoring the database
- rerunning migrations
- redeploying updated versions

## Current deployment limitations

The current deployment is a working MVP deployment, but not yet a fully polished production environment.

Not-yet-finalized infrastructure items include:

- HTTPS
- custom domain
- stronger production hardening
- more powerful server sizing
- automated backup scheduling
- uptime monitoring

## Why deployment matters for this project

Deployment is an important part of the project because it turns the application from a local development exercise into a real accessible system.

That greatly improves the value of the project as:

- a study deliverable
- a portfolio project
- a practical operational demo