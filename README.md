# Husky Tracking AI

Husky Tracking AI is a full-stack web application for tracking sled dog workload, daily operational status, kennel-level planning signals, and team composition support.

The project was designed as a practical operational tool for husky management and as a study project focused on turning real-world kennel routines into a structured digital system.

## Project purpose

The goal of the project is to replace fragmented Excel-based workflows with a centralized web application that supports:

- daily work logging
- dog status and operational planning
- analytics by period and by week
- workload visibility and risk detection
- support for building balanced sled teams
- practical exports for managers and field use

## Core features

### Dashboard
- operational overview of the kennel
- heatmap view
- watchlist
- planning blockers
- underused dogs
- quick visibility into current planning state

### Dog management
- dog profiles
- operational information
- lifecycle and availability statuses
- archive support
- exclusion flags for planning logic
- role-related information for lead, team, and wheel positions

### Daily Entry
- daily logging of dog work
- save and reload entries by date
- worked / not worked logic
- kilometers and program-related data

### Team Builder
- automatic team suggestion based on business logic
- support for role-aware harness layout
- risk / workload / eligibility-based filtering
- underused dog preference
- compact printable team sheet for field use

### Analytics
- total km by week
- worked dogs by week
- high / moderate / underused weekly snapshots
- average km per worked dog
- week comparison
- period filtering
- export-oriented analytics structure

### Export
- Excel export for analytics
- CSV export for raw run logs
- PDF analytics summary
- compact printable team layout

## Tech stack

### Backend
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Matplotlib
- Docker

### Frontend
- Angular
- TypeScript
- SCSS

### Deployment
- Docker Compose
- Nginx
- VPS deployment

## Architecture overview

The system is split into three main layers:

- **Frontend**: Angular application for operational UI, analytics, planning, and exports
- **Backend**: FastAPI service exposing domain-specific endpoints for dashboard, dogs, worklogs, analytics, exports, and team-building logic
- **Database**: PostgreSQL database storing dog metadata and work logs

The production deployment uses:

- Nginx for serving the frontend
- reverse proxy routing to backend API under `/api/v1`
- Docker containers for frontend, backend, and database

## Main domain logic already implemented

The application already includes a meaningful amount of domain-specific logic, including:

- workload visibility
- risk classification
- eligibility logic
- exclusion logic
- underuse detection
- weekly analytics aggregation
- harness-aware team layout generation

This makes the project more than just a CRUD application. It is an operational planning system with real domain rules.

## Local development

### Requirements
- Docker
- Docker Compose

### Run locally

```bash
docker compose up -d --build
```

Then open the application in the browser.

## Production deployment

A production-style deployment is configured with:

- `docker-compose.prod.yml`
- frontend served via Nginx
- backend running in production mode
- PostgreSQL in Docker
- backup and restore workflow documented in `OPERATIONS.md`

## Operations

Basic deployment and maintenance commands are documented in:

`OPERATIONS.md`

This includes:

- connecting to the server
- checking service status
- viewing logs
- rebuilding containers
- database backup
- database restore
- migrations

## Current project status

The current state of the project can be treated as an MVP that already supports:

- real operational workflow
- persistent data storage
- analytics and export
- team suggestion logic
- production deployment on VPS

## Future improvements

### Infrastructure and deployment

- improve deployment with HTTPS
- purchase and configure a cleaner custom domain
- move the application to a more powerful server if usage grows

### Product and security

- add authentication / login service
- improve data security and access control
- review and strengthen overall data protection approach

### Dog data management

- add dog photo upload service
- consider cloud-based data storage strategy

### Seasonal workflow support

- add offseason mode
- add autumn training season mode
- support different operational modes across the year

### Planning and scheduling

- add full-day program layers
- model daily program structure more explicitly
- adapt Team Builder to full working-day program scenarios instead of isolated single-build runs

### Data quality and testing

- continue validating business logic with real operational use
- improve test coverage
- keep testing and refining planning logic over time

### Advanced data integration

- explore integration with collar API data
- use more precise activity and force-related data
- improve workload measurement accuracy
- support a more objective strength estimation system for dogs
- use this data to help Team Builder create more balanced teams

## Why this project matters

This project combines:

- real operational needs
- domain modeling
- full-stack engineering
- analytics
- export workflows
- deployment and maintenance

It is both a practical kennel-management tool and a substantial software engineering project.

## Author

Oleg Shaltaev