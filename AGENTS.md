# AGENTS.md — NEXUS Engineering Constitution

> NEXUS is a production-oriented engineering intelligence platform.
> This file is the engineering constitution for the repository.

## Current Architecture

- frontend: existing HTML/CSS/JavaScript prototype
- backend: FastAPI
- ORM: SQLAlchemy 2.x
- migrations: Alembic
- database: PostgreSQL
- queue/cache: Redis
- deployment: Docker
- initial cloud target: Render
- architecture: modular monolith
- no microservices for v1

## Important Product Rule

The existing NEXUS frontend is the visual contract.

Do not redesign it while implementing backend functionality.

Preserve:

- JetBrains Mono
- dark monochrome visual language
- thin borders
- dense information layout
- technical typography
- keyboard-first navigation
- command palette
- sparse charts
- evidence-oriented presentation

## Architecture Rules

1. Keep one deployable FastAPI application for v1.
2. Do not introduce microservices.
3. Keep business logic out of route handlers.
4. Keep database access out of frontend code.
5. Use service/domain layers.
6. Use SQLAlchemy models for persistence.
7. Use Pydantic schemas at API boundaries.
8. All tenant-owned data must eventually be scoped through `workspace_id`.
9. Never expose GitHub credentials to the browser.
10. Never use personal GitHub access tokens for the product.
11. GitHub repository access must use a GitHub App.
12. GitHub webhook handling must be authenticated and idempotent.
13. Background ingestion must be retryable.
14. External GitHub IDs are separate from NEXUS UUID primary keys.
15. LLM output must never directly determine risk scores.
16. Risk scores must come from deterministic/ML signals.
17. AI analyst must use controlled tools.
18. AI analyst must not execute arbitrary SQL.
19. Never fabricate engineering data.
20. Never silently replace real data with mock data once an API exists.

## Development Rules

Before changing code:

- inspect the relevant files
- understand existing architecture
- make the smallest change necessary

After changing code:

- run relevant tests
- run lint/type checks if configured
- verify the application starts
- report exactly what changed

Do not:

- rewrite unrelated files
- rename the frontend architecture without reason
- introduce dependencies without justification
- build speculative abstractions
- implement future phases early

Each task must have a narrow scope.

When a task is complete, STOP.

## Report

- files changed
- implementation summary
- tests run
- test results
- remaining concerns