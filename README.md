# ResolveAI

ResolveAI is an autonomous AI customer support platform built with FastAPI, LangChain, PostgreSQL, and Next.js.

## Backend

- FastAPI async API server
- Autonomous ticket processing agent
- RAG-powered knowledge retrieval
- PostgreSQL + pgvector storage

## Getting started

1. Install backend dependencies:
   ```bash
   cd backend
   python3 -m pip install -r requirements.txt
   ```
2. Run the backend service:
   ```bash
   uvicorn backend.main:app --reload
   ```

## Project structure

- `backend/` — Python API, agent, RAG, database models
- `frontend/` — Next.js dashboard and ticket UI
- `shared/` — shared utilities and types

