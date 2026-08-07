# CreatorShield

CreatorShield is a Docker Compose monorepo for registering original Reels and generating technical Creator Proof records.

## Run locally

```bash
docker compose up --build
```

Open [http://localhost:3000](http://localhost:3000). The FastAPI docs are at [http://localhost:8000/docs](http://localhost:8000/docs).

The Compose profile runs PostgreSQL, Valkey, the FastAPI API, a background worker, and the Next.js frontend. Local filesystem storage is used by default for private uploads; the API also contains an S3-compatible storage adapter for Zerops deployment.
