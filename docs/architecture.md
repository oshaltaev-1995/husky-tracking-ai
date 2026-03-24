# Architecture draft

## MVP modules
- Dog registry
- Daily worklog import
- Dashboard metrics
- Dog profile
- Red flags / fatigue rules
- Team builder

## Backend layers
- api
- schemas
- services
- repositories
- models
- db

## Data flow
Excel -> import service -> PostgreSQL -> FastAPI -> Angular
