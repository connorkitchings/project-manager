# API Documentation

The API surface for Project Manager is still draft-level, but the intended shape is straightforward.

## Purpose

Expose normalized repo status snapshots to the web UI and provide a simple way to refresh tracked repositories.

## Implemented Endpoints

- `GET /` - Frontend application shell
- `GET /api/meta` - Health/info response with persistence and config paths
- `GET /api/tracked-repos` - List all tracked repos, including disabled ones
- `POST /api/tracked-repos` - Add a tracked repo after validating the GitHub repository
- `PATCH /api/tracked-repos/{repo_id}` - Update tracked repo runtime fields such as enabled/name/notes
- `GET /api/repos` - List tracked repositories with summary status fields
- `GET /api/repos/{repo_id}` - Get the full normalized snapshot for one tracked repo
- `POST /api/sync` - Trigger a refresh of all enabled tracked repos

## Current Backend MVP

The first backend implementation is now in place:

- Flask-based API service
- React SPA built and served by Flask
- YAML tracked repo bootstrap in `config/tracked_repos.yaml`
- SQLite-backed app state for tracked repos, latest snapshots, and sync runs
- Settings UI at `/settings/repos` for add + enable/disable management
- On-demand sync only
- Repository docs as the primary status source, GitHub activity as supporting evidence

## Authentication

No dedicated end-user auth is planned for v1. This is a single-user internal tool. Any GitHub credential handling belongs to the app environment, not the public API surface.

## Notes

- The API should return normalized status fields, not raw markdown blobs.
- Missing documentation should surface as structured gaps or warnings.
- Attention states include human-readable `attention_reasons` alongside `attention_flag`.
- Runtime state comes from SQLite; YAML is an early-stage seed source, not the long-term system of record.
- Only enabled repos participate in `/api/repos` and `/api/sync`; disabled repos remain available through tracked-repo management endpoints.
- The OpenAPI file in this directory is a draft contract and should evolve with implementation.
