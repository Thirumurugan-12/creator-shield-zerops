# CreatorShield · Zerops Challenge runbook

## The 30-second pitch

Creators need a reliable trail when an original Reel is copied, modified, or used in a suspicious complaint. CreatorShield turns an upload into a private Creator Proof: SHA-256, media metadata, keyframe perceptual hashes, audio fingerprint, processing events, and an honest transcript-unavailable state. A later Incident compares the original with a suspicious copy and generates a transparent technical evidence report.

## Why Zerops is meaningful

CreatorShield is intentionally split across Zerops services:

```text
Web (Next.js) → API (FastAPI) → Worker (FFmpeg + comparison)
                         ↘ PostgreSQL
                         ↘ Valkey queue
                         ↘ private object storage
```

- The API accepts and authorizes uploads; long-running media work is sent to the worker.
- Valkey decouples the request from FFmpeg and comparison processing.
- PostgreSQL persists proof, incident, event, and report context across redeploys.
- Private object storage keeps originals and evidence files out of public buckets.
- Zerops service scaling is visible in the separate web/API/worker boundaries.

## Deploy from a clean checkout

1. Create or select a Zerops project and authenticate `zcli`.
2. Import [`zerops-import.yaml`](../../zerops-import.yaml).
3. Add the secret and managed-service values from [`infra/zerops/README.md`](../../infra/zerops/README.md) to the API and worker.
4. Set `CREATORSHIELD_WEB_URL` and `CREATORSHIELD_API_URL` to the public HTTPS hostnames.
5. Push API, worker, then web using the commands in the root README.
6. Check `https://<api-host>/health` and open `https://<web-host>`.

## Live demo checklist

- Register a short MP4 and show the progress event stream.
- Open the proof technical evidence tab and show the SHA-256 and keyframes.
- Create an incident with the same video as a controlled comparison fixture.
- Show similarity scores, modification indicators, and the explicitly simulated community label.
- Open Reports and download the PDF.
- Show that a signed media URL works while the underlying object-storage bucket remains private.

## Submission evidence

Capture the public repository, deployed URL, a short demo video, and a brief architecture explanation. State exactly where Zerops is used: service topology, worker scaling, managed data services, private storage, migration startup, and production environment configuration. Do not describe simulated community data or technical similarity as legal conclusions.

## Rollback

Record the commit SHA and Alembic revision for every release. If a release fails, push the previous known-good commit to the affected setup, verify `/health`, then confirm one proof and one report flow before reopening the live URL for judging.
