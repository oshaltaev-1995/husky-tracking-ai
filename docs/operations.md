# Operations

## Production server
- Server IP: `89.124.87.216`
- Project path on server: `/root/husky-tracking-ai`

## Connect to server

```bash
ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=120 root@89.124.87.216
```

## Check container status

```bash
cd /root/husky-tracking-ai
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

## Database checks

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

> Run on Mac terminal, not on the server:

```bash
scp root@89.124.87.216:/root/backups/husky_tracking_YYYY-MM-DD_HH-MM-SS.sql ~/Downloads/
```

## Restore database from backup

### Clear current schema

```bash
cd /root/husky-tracking-ai
docker compose -f docker-compose.prod.yml exec db \
  psql -U husky -d husky_tracking -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
```

### Restore dump

```bash
cat /root/backups/FILE_NAME.sql | docker compose -f docker-compose.prod.yml exec -T db \
  psql -U husky -d husky_tracking
```

### Restart backend

```bash
docker compose -f docker-compose.prod.yml restart backend
```

## Run migrations

```bash
docker compose -f docker-compose.prod.yml exec backend sh -c "cd /app && alembic upgrade head"
```

## If the site opens but API fails

Check:

- backend logs
- db logs
- that tables exist
- that dogs/worklogs counts are not zero