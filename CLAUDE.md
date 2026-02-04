# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a personal workout tracking system that pulls heart-rate data from the Polar AccessLink API, matches workouts with video sources (YouTube, FitOn), stores everything in PostgreSQL, and exposes a query API via Google Cloud Functions. The repo uses **Sapling** (not git) for version control.

## Development Setup

- **Python 3.10** (see `.python-version`), managed with **Poetry**
- Activate the virtual env: `poetry shell`
- Install dependencies: `poetry install`
- Formatting: `black` and `isort` (isort uses the "black" profile)

## Running Tests

Tests use `unittest` with `testing.postgresql` (spins up a real temporary PostgreSQL instance). All test files follow the `test_*.py` naming convention.

```bash
# Run all tests
python -m pytest src/

# Run a single test file
python -m pytest src/api/tests/test_api.py

# Run a single test
python -m pytest src/api/tests/test_api.py::TestAPIClass::test_method
```

Test locations:
- `src/api/tests/` — API layer tests
- `src/db/workout/tests/` — workout DB model tests
- `src/workout_sources/tests/` — video source parsing tests

The test base class is `src/utils/test_base.py:TestBase`, which sets up a temporary PostgreSQL database with fixture data (defined in `src/utils/test_db.py`). Tests that need a database should inherit from `TestBase` and call `cls.create_test_db()` in `setUpClass`.

## Running Scripts

```bash
python -m src.scripts.name_of_script
```

## Local API Testing

Requires GCP Cloud SQL Auth Proxy running:
```bash
cloud_sql_proxy --credential_file=creds.json --dir=/cloudsql/
```

Test API functions locally with `functions-framework`:
```bash
cd src/api_functions
functions-framework --target sources_http
# Then: curl http://localhost:8080
```

## Architecture

### Two Cloud Functions (deployed via Serverless Framework)

1. **`src/api_functions/`** — Read-only query API. Entry points in `main.py` expose HTTP handlers (`workouts_http`, `sources_http`, `tags_http`, `equipment_http`, `exercises_http`, `everything_http`). Each handler instantiates `API`/`QueryAPI`/`TagAPI` from `src/api/` and delegates to `DBBase` for database queries.

2. **`src/refresh_function/`** — Data ingestion. Pulls new exercises from Polar API, matches them with video sources from the `source_input` DB, and saves to the `workouts` DB. Entry point: `main.py:http`. Uses `ProcessData` in `polar.py` to coordinate the pipeline.

### Database Layer (`src/db/`)

Uses **Peewee ORM** with `playhouse.postgres_ext` for PostgreSQL-specific types.

- **Two separate databases** connected via `src/utils/db_utils.py:DBConnection`:
  - `workouts` DB — main data store (`src/db/workout/models.py`)
  - `source_input` DB — raw source input (`src/db/sources/models.py`)
- Key models: `Workouts`, `Sources`, `Equipment`, `Tags` with many-to-many relationships
- **Materialized views**: `WorkoutsMaterialized` and `SourcesMaterialized` flatten the many-to-many joins for efficient API reads. Created from SQL in `src/db/workout/sql/`. Refreshed after each data ingestion.
- `BaseModel` (`src/db/base_model.py`) provides `as_dict()` and `json_friendly()` for serialization.

### API Query Layer (`src/api/`)

- `api.py` — `API`, `TagAPI`, `QueryAPI` classes handle request parsing, pagination, and response formatting
- `complex_query.py:ComplexQuery` — builds Peewee query expressions from structured `Query` objects (supports filtering by sport, equipment, HR zones, source tags, date ranges, etc.)
- `db_base.py:DBBase` — executes queries against materialized views with pagination

### Swagger/OpenAPI Models (`swagger_server/`)

Auto-generated from OpenAPI spec (via `.openapi-generator`). The `swagger_server/models/` define API request/response types (e.g., `Query`, `SourceType`, `EquipmentType`, `ZoneType`). These are used for request validation in `QueryAPI`.

### Workout Sources (`src/workout_sources/`)

Parsers for video workout platforms. `youtube.py` extracts video IDs from URLs and fetches metadata. `fiton.py` handles FitOn workouts. `source_consts.py` contains mappings of known workout sources.

### Configuration

- `app_config.json` — DB connection settings and feature flags (gitignored; each function dir has its own copy)
- `src/utils/config.py` — reads `app_config.json` (cached)
- `secrets.yml` — GCP credentials paths (gitignored)
- DB connections go through Unix sockets via Cloud SQL Proxy (`/cloudsql/`)

### Import Style

All internal imports use absolute paths from the repo root: `from src.db.workout import models`, `from src.api.api import API`, etc.
