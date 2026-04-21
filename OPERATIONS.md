# Husky Tracking AI — Operations Guide

## Production server
- Server IP: `89.124.87.216`
- App URL: `http://89.124.87.216`
- Project path on server: `/root/husky-tracking-ai`

---

## Connect to server

```bash
ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=120 root@89.124.87.216
```

## Go to project folder

```bash
cd /root/husky-tracking-ai
```

## Check container status

```bash
docker compose -f docker-compose.prod.yml ps
```

## View logs

### Backend

```bash
docker compose -f docker-compose.prod.yml logs backend --tail=100
```

### Frontend

```bash
docker compose -f docker-compose.prod.yml logs frontend --tail=100
```

### Database

```bash
docker compose -f docker-compose.prod.yml logs db --tail=100
```

## Restart services

### Restart all

```bash
docker compose -f docker-compose.prod.yml restart
```

### Restart backend only

```bash
docker compose -f docker-compose.prod.yml restart backend
```

### Restart frontend only

```bash
docker compose -f docker-compose.prod.yml restart frontend
```

## Start app again if needed

```bash
docker compose -f docker-compose.prod.yml up -d
```

## Update deployment after pushing new code

```bash
cd /root/husky-tracking-ai
git pull
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

## Rebuild from scratch

```bash
cd /root/husky-tracking-ai
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
```

## Check database contents

### List tables

```bash
docker compose -f docker-compose.prod.yml exec db psql -U husky -d husky_tracking -c "\dt"
```

### Count dogs

```bash
docker compose -f docker-compose.prod.yml exec db psql -U husky -d husky_tracking -c "select count(*) from dogs;"
```

### Count worklogs

```bash
docker compose -f docker-compose.prod.yml exec db psql -U husky -d husky_tracking -c "select count(*) from worklogs;"
```

## Create backup

```bash
cd /root/husky-tracking-ai
mkdir -p /root/backups
docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U husky -d husky_tracking > /root/backups/husky_tracking_$(date +%F_%H-%M-%S).sql
ls -lh /root/backups
```

## Download backup to Mac

> Run this on your Mac terminal, not on the server:

```bash
scp root@89.124.87.216:/root/backups/husky_tracking_YYYY-MM-DD_HH-MM-SS.sql ~/Downloads/
```

### Example:

```bash
scp root@89.124.87.216:/root/backups/husky_tracking_2026-04-21_10-47-39.sql ~/Downloads/
```

## Restore database from backup

### 1. Clear current schema

```bash
cd /root/husky-tracking-ai
docker compose -f docker-compose.prod.yml exec db \
  psql -U husky -d husky_tracking -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
```

### 2. Restore dump

```bash
cat /root/backups/FILE_NAME.sql | docker compose -f docker-compose.prod.yml exec -T db \
  psql -U husky -d husky_tracking
```

### 3. Restart backend

```bash
docker compose -f docker-compose.prod.yml restart backend
```

## Run migrations

```bash
docker compose -f docker-compose.prod.yml exec backend sh -c "cd /app && alembic upgrade head"
```

## If site opens but API fails

Check:
- backend logs
- db logs
- database tables exist
- dogs/worklogs counts are not zero

### Useful commands:

```bash
docker compose -f docker-compose.prod.yml logs backend --tail=200
docker compose -f docker-compose.prod.yml logs db --tail=100
docker compose -f docker-compose.prod.yml exec db psql -U husky -d husky_tracking -c "\dt"
docker compose -f docker-compose.prod.yml exec db psql -U husky -d husky_tracking -c "select count(*) from dogs;"
docker compose -f docker-compose.prod.yml exec db psql -U husky -d husky_tracking -c "select count(*) from worklogs;"
```

## If server rebooted

Usually containers should come back automatically because services use `restart: unless-stopped`.

Still, if needed:

```bash
ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=120 root@89.124.87.216
cd /root/husky-tracking-ai
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml ps
```

## Current production notes

- Frontend is served by nginx in Docker
- Backend is FastAPI in Docker
- Database is Postgres in Docker
- Frontend calls backend via `/api/v1`
- Production compose file: `docker-compose.prod.yml`

## Recommended next improvements

- Remove backend auto-reload from production startup
- Add domain
- Add HTTPS
- Set up scheduled database backups
- Add project documentation / GitHub Pages