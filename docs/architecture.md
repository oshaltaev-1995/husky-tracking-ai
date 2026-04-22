# Architecture

## Overview

Husky Tracking AI is a full-stack web application built around three core layers:

- Angular frontend
- FastAPI backend
- PostgreSQL database

The system is deployed in containers and exposed through Nginx, which serves the frontend and proxies API requests to the backend.

## High-level structure

The architecture follows a standard client-server model:

1. the user interacts with the Angular frontend
2. the frontend sends HTTP requests to backend API endpoints under `/api/v1`
3. the FastAPI backend executes business logic
4. the backend reads from and writes to PostgreSQL
5. the backend returns structured JSON responses to the frontend
6. the frontend renders operational views, analytics, team suggestions, and export actions

## Frontend

The frontend is implemented with Angular and acts as the operational user interface of the system.

Main responsibilities:

- rendering dashboard views
- displaying dog data and statuses
- handling daily entry workflows
- presenting analytics and charts
- requesting export files from the backend
- displaying team builder results
- providing compact print layout for teams

The frontend uses a relative API base path:

- `/api/v1`

This makes the application easier to deploy behind a reverse proxy.

## Backend

The backend is implemented with FastAPI and contains the main application logic.

Main responsibilities:

- exposing REST API endpoints
- validating and processing requests
- handling domain logic for dogs, worklogs, analytics, and team builder
- generating export files
- interacting with the database through SQLAlchemy
- applying database schema evolution through Alembic migrations

The backend is the main place where domain-specific planning and aggregation logic lives.

## Database

The database layer uses PostgreSQL.

Main stored data includes:

- dog records
- worklogs
- operational metadata
- status-related information used by dashboard and planning features

PostgreSQL was chosen because it is reliable, well-supported, and suitable for structured relational data.

## API structure

The API is exposed under:

- `/api/v1`

The backend includes endpoint groups for areas such as:

- dashboard
- dogs
- worklogs
- analytics
- exports
- team builder

This separation keeps the application modular and easier to extend.

## Domain logic placement

A key architectural decision in the project is to keep domain logic primarily in the backend instead of the frontend.

Examples include:

- workload classification
- underuse detection
- eligibility logic
- exclusion logic
- weekly aggregation
- team-building support logic
- export generation

This keeps business rules centralized and reduces the risk of inconsistent behavior across views.

## Analytics architecture

The analytics feature is built around backend-side aggregation and frontend-side presentation.

### Backend responsibilities
- calculate weekly aggregates
- compare selected weeks
- produce export-ready datasets
- generate Excel, CSV, and PDF output

### Frontend responsibilities
- request analytics data for selected periods
- render charts and summary cards
- handle export actions
- present comparison UI

This split keeps the frontend lighter and prevents duplication of aggregation logic.

## Export architecture

Exports are generated on the backend.

Current export types include:

- Excel workbook
- CSV raw run logs
- PDF summary

This design is preferable because:

- formatting can be centralized
- file generation logic is reusable
- exported data remains consistent with backend calculations

For Team Builder, a compact print-oriented layout is currently handled on the frontend for practical browser printing.

## Deployment architecture

The deployed environment uses Docker containers for each main service:

- frontend container
- backend container
- database container

Nginx is used inside the frontend container to:

- serve static Angular build files
- proxy `/api/v1` requests to the backend container

This gives a clean deployment model where the frontend and backend are exposed under the same public host.

## Production flow

In production, the request flow looks like this:

1. browser requests the application from the public server
2. Nginx serves the Angular frontend
3. frontend requests `/api/v1/...`
4. Nginx forwards API traffic to the backend container
5. backend queries PostgreSQL and returns data
6. frontend renders the result

## Database lifecycle

The database schema is managed through Alembic migrations.

This means:

- empty production databases can be initialized through migrations
- schema changes can be versioned
- deployment is safer than relying only on manual table creation

Data persistence is handled through Docker volumes.

## Operational characteristics

The current architecture is suitable for:

- MVP deployment
- portfolio demonstration
- limited real operational use
- iterative feature expansion

It is intentionally simple enough to manage on a VPS while still reflecting real full-stack engineering practices.

## Current limitations

The architecture is functional, but there are still areas for future improvement:

- no authentication layer yet
- no HTTPS yet
- no automated backup scheduling yet
- no dedicated cloud media storage yet
- no external collar API integration yet

## Future architectural direction

Possible future architectural improvements include:

- authentication and role-based access
- media storage for dog photos
- cloud-based storage strategy
- stronger production hardening
- collar API integration
- more advanced planning workflows for full-day scheduling
- broader seasonal operating modes

## Summary

The architecture of Husky Tracking AI is intentionally practical:

- simple enough for MVP delivery
- structured enough for real deployment
- flexible enough for future extensions

It supports the main project goal: turning real kennel operations into a usable digital planning and analytics system.