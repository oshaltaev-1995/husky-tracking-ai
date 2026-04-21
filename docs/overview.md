# Project Overview

## What is Husky Tracking AI?

Husky Tracking AI is a domain-focused operational system for managing sled dog workload, kennel visibility, daily activity logging, and team-planning support.

It was designed around a practical problem: operational dog data was being tracked in fragmented ways, mostly through spreadsheet logic, which made it difficult to maintain a clear overview, compare periods, and build consistent teams based on actual workload and status.

## Main goal

The main goal of the project is to transform kennel operations into a more structured digital workflow.

This includes:

- replacing scattered spreadsheet processes
- centralizing dog-related operational data
- improving visibility of workload and usage
- supporting more informed team-building decisions
- making weekly and period-based analytics easier to access
- improving export and communication with managers and field staff

## Why this project is meaningful

This is not just a CRUD system. The project includes actual domain logic such as:

- workload awareness
- eligibility logic
- exclusion logic
- underuse detection
- risk-related planning signals
- harness-aware team layout support
- compact field-oriented print output

Because of that, the project combines:
- software engineering
- operational planning
- analytics
- reporting
- deployment
- long-term product thinking

## Target use

The system is intended to support real kennel operations, including:

- daily work logging
- status-based dog planning
- weekly review of activity and load
- manager-facing summaries
- field-friendly team printouts
- data-driven improvement of team composition logic over time

## Architectural model

The application is built as a standard full-stack system:

- **Angular frontend** for operational UI and user interaction
- **FastAPI backend** for business logic, API endpoints, analytics, exports, and planning logic
- **PostgreSQL database** for dog and worklog persistence
- **Docker-based deployment** for reproducible local and server environments

## MVP scope

The MVP already includes the main building blocks needed for a meaningful demonstration and practical use:

- Dashboard
- Dog management
- Daily Entry
- Team Builder
- Analytics
- Export
- Production deployment on VPS

## Current direction

At this stage, the project already works as a deployed MVP.

The next major direction is not only polish, but also extension toward:

- stronger deployment quality
- stronger documentation
- more robust security and access control
- richer seasonal planning workflows
- more accurate dog-performance data inputs