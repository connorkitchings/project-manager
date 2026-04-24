# Web Architecture Guide

## Overview

This guide establishes architectural patterns for the Project Manager web application. The goal is to keep the repo status dashboard simple in v1 while leaving room to grow without a rewrite.

## Core Rules

### 1. Headless-First
**Principle:** The API is the product; the UI is just a consumer.
-   Build your backend logic as a standalone Flask API first.
-   Ensure your model/logic can be run via CLI or Cron without the web server.
-   *Why?* Decoupling ensures your core logic remains portable and testable.

### 2. Component Silo
**Principle:** The Frontend must never touch the Database directly.
-   **Forbidden:** Importing backend storage modules or reading SQLite directly from React code.
-   **Required:** Fetch data via the Flask API (`/api/...`).
-   *Why?* Direct DB access from UI components creates a monolithic web of dependencies that is hard to refactor.

### 3. Server-Side State Strategy
**Principle:** Prefer Server State tools over complex Client State stores.
-   **Recommended:** TanStack Query (React Query) or SWR.
-   **Discouraged:** Redux, mobx, or heavy Zustand stores for simple data fetching.
-   *Why?* "Vibe coding" often leads to over-engineered state management. Keep it simple: invalidating a query is easier than managing a reducer.

## Recommended Stack

| Layer | Tool | Note |
|-------|------|------|
| **Backend** | Flask | Existing API layer and asset host |
| **Frontend** | Vite + React + TypeScript | Separate UI app compiled into Flask-served assets |
| **API Client** | TanStack Query | Cache and invalidation for repo/meta/sync requests |
| **Styling** | Tailwind CSS | Utility-first styling with light design-token theming |

## Directory Structure

```text
project/
├── src/                # Backend / Core Logic
│   └── project_manager/
│       ├── api/        # Flask app and route handlers
│       └── services/   # Sync, registry, and persistence logic
├── ui/                 # Frontend application
│   ├── src/
│   │   ├── app/
│   │   ├── features/
│   │   └── lib/
│   └── package.json
└── docs/
    └── guides/
        └── web_architecture.md
```
