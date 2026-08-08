# CreatorShield

CreatorShield is an open-source, Zerops-deployed evidence platform for creators. It registers original Reels, processes durable technical proof in a worker, compares suspicious copies, and produces an explainable evidence report.

## Hackathon deployment

The project is designed for the Zerops Challenge: the deployment is part of the product, not a side demo. `zerops-import.yaml` provisions the full service topology and `zerops.yaml` builds and runs the web, API, and worker setups.

```bash
zcli project project-import zerops-import.yaml
zcli service push --setup api
zcli service push --setup worker
zcli service push --setup web
```

Before pushing, configure the managed PostgreSQL, Valkey, and private object-storage credentials listed in [`infra/zerops/README.md`](infra/zerops/README.md). Keep the public web and API hostnames in `CREATORSHIELD_WEB_URL` and `CREATORSHIELD_API_URL`; the API runs migrations before startup and uses signed/private media access.

Judge demo path: open the web URL → Secure a Reel → wait for the worker to produce a Creator Proof → create an Incident → review comparison/community signals → preview and download the technical-only PDF report. The complete submission runbook is in [`docs/hackathon/README.md`](docs/hackathon/README.md).

## Run locally

```bash
docker compose up --build
```

Open [http://localhost:3000](http://localhost:3000). The FastAPI docs are at [http://localhost:8000/docs](http://localhost:8000/docs).

The Compose profile runs PostgreSQL, Valkey, the FastAPI API, a background worker, and the Next.js frontend. Local filesystem storage is used by default for private uploads; the API also contains an S3-compatible storage adapter for Zerops deployment.

## Verification

```bash
docker compose config --quiet
cd apps/web && npm run build
cd ../..
PYTHONPATH=. pytest -q apps/api/tests
```
