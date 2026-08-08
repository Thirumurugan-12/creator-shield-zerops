# CreatorShield Consistency Guide

This document records the rules to follow when changing CreatorShield. Update it when a new architectural or product convention is introduced.

## Repository boundaries

- Frontend code belongs in `apps/web`.
- Backend code belongs in `apps/api`.
- Shared contracts and generated types belong in `packages/shared`.
- Deployment and infrastructure configuration belongs in `infra` or the root Compose files.
- Do not place backend business logic in frontend route components.
- Do not place presentation logic in FastAPI route handlers.

## Frontend stack

- Use Next.js App Router and TypeScript strict mode.
- Use Tailwind semantic classes and CSS variables; do not scatter arbitrary color hex values through components.
- Use Lucide icons consistently.
- Use React Hook Form plus Zod for user-entered forms.
- Use TanStack Query for API-backed data and polling.
- Use `next-themes` for theme switching.
- Use Sonner for mutation feedback and errors.
- Prefer shadcn/ui and Radix-based primitives for controls, dialogs, tabs, tables, forms, and feedback.
- Keep reusable UI primitives in `apps/web/components/ui/` and export stable application-facing names through `components/ui.tsx`.
- Use `focus-visible` styles, semantic roles, and live regions for interactive and asynchronous states.
- Loading, empty, error, and retry states should be shared components rather than repeated ad hoc markup.
- Avoid adding component libraries outside the approved stack.

## Visual language

- The product should feel precise, trustworthy, quiet, and evidence-first.
- Prefer restrained borders and spacing over gradients, glow, or decorative effects.
- Use `rounded-md` for controls and `rounded-xl` for panels/cards.
- Use monospace typography for proof IDs, hashes, timestamps, event logs, and technical metadata.
- Every status must include a text label; color must never be the only indicator.
- Use semantic status tokens: secured, processing, review, high risk, critical, evidence match, and evidence neutral.
- Keep authenticated page titles compact and information-dense.
- Do not create fabricated analytics, risk scores, incidents, or processing output.

## Data and evidence integrity

- Treat publication dates, URLs, usernames, captions, and notes as user-provided unless independently verified.
- Never present a technical similarity result as a legal ownership determination.
- Use language such as `High suspicion`, `Potential pattern detected`, and `Payment demand detected`.
- Do not use language such as `Fraud confirmed`, `Criminal detected`, or `Illegal copyright claim`.
- All evidence scores must expose the underlying evidence or rule inputs.
- Hashes must be rendered in monospace and provide access to the complete value.
- Empty, unavailable, and failed processing states must be explicit rather than filled with invented values.

## API conventions

- Use `/api/...` for application endpoints.
- Return stable snake_case field names from FastAPI.
- Validate uploads on the backend even when the frontend validates them first.
- Enforce file type and size limits before persisting the upload.
- Keep long-running media work out of synchronous request handling.
- Emit timestamped processing events for user-visible progress.
- Keep storage private and expose media through controlled URLs.
- Add or update a test when adding a backend endpoint or changing its contract.

## Authentication conventions

- The current MVP uses the PRD-approved demo creator fallback; do not imply that email/password registration is implemented yet.
- Session tokens must be signed, short-lived, stored in an HTTP-only cookie, and never exposed to frontend JavaScript.
- Authenticated API requests must use `credentials: "include"`.
- Every proof, incident, media, and report query must be scoped to the current user.
- Public routes are limited to the landing page, login, health, and authentication entry points.
- Logout must clear the session cookie and invalidate the frontend query cache.
- Unauthorized UI must redirect to login with a clear, non-destructive message.

## Processing conventions

The intended Creator Proof pipeline is:

```text
Upload secured
→ Metadata extracted
→ SHA-256 fingerprint generated
→ Keyframes extracted
→ Audio fingerprint generated
→ Transcript checked
→ Creator Proof finalised
```

- Status values should be stable and lower-case in the API: `processing`, `secured`, and `failed`.
- Progress must reflect actual completed work; do not simulate finished evidence as available.
- Provider-dependent features should use an explicit unavailable fallback during local development.
- Worker retries must be safe to repeat without corrupting an existing proof.

## Documentation and tracking

- Update `master_todo.md` when work is completed, deferred, or newly discovered.
- Update the change log in `master_todo.md` for meaningful implementation milestones.
- Update this file when a new convention is established or an existing convention changes.
- Keep README setup instructions aligned with `docker-compose.yml` and the actual environment variables.
- Mention verification results and known environment blockers in handoff notes.

## Current known limitations

- The local backend persists proof records with SQLAlchemy and stores files in a local volume by default.
- PostgreSQL, Valkey, a worker service, and an S3-compatible adapter are configured; Docker runtime verification is still pending.
- Signed media URLs, media metadata, keyframes, audio fingerprints, and comparison outputs are extracted from local video content when ffmpeg/ffprobe are available.
- Zerops builds install and prefetch the pinned `static-ffmpeg` package so both `ffmpeg` and `ffprobe` are available even when the native Python runtime has no OS media packages. The application resolves system binaries first and falls back to the bundled static binaries.
- Transcript extraction remains an explicit unavailable state until a provider is configured; side-by-side matching keyframes and advanced crop, watermark, speed, and color indicators are still pending.
- Complaint originals remain private evidence files; extracted complaint fields and suspicion indicators are persisted separately. Local PDF text extraction is supported, while image OCR remains an explicit unavailable state.
- Community intelligence is simulated development data only. It must be labelled in the UI, kept separate from uploaded evidence, and explain the exact correlating identifier before affecting a review score.
- Evidence reports must use the same persisted incident context for preview and PDF download, call out missing information, include the technical-only disclaimer, and record a download activity event.
- Uploads must pass extension, content-signature, size, safe-filename, and storage-key checks before persistence. Malware scanning is an explicit integration hook until a scanner is configured.
- Production deployments must set `SECURE_COOKIES=true`, strong session/media secrets, and an explicit `CORS_ORIGINS` list. Local development may use HTTP-only cookies over localhost with `SECURE_COOKIES=false`.
- Zerops deployment uses `zerops-import.yaml` for infrastructure and `zerops.yaml` for application pipelines. Do not mark production deployment complete until the authenticated project smoke test passes.
- Keep `zerops.yaml` and `zerops.yml` aligned when both are present; Zerops Git/repository triggers may consume the YAML manifest while legacy UI labels refer to `zerops.yml`.
- For browser API calls, treat `/api` as a same-origin prefix rather than an API origin; never concatenate it with another `/api` segment.
- The native Zerops Python service uses `python -m uvicorn` and includes the PostgreSQL driver selected by the deployed connection URL.
- Hackathon-facing navigation routes must be functional: Reports reads incident records, Community Intelligence exposes only labelled simulated signals, and Settings reads the authenticated profile and controls appearance.
- Submission documentation must explain why Zerops is materially involved in the product architecture, not merely name it as a hosting provider.
- Docker Compose has been configured but requires a running Docker daemon for container execution.
- The Zerops incident comparison path must not require a native FFmpeg executable: PyAV with NumPy is the runtime fallback for frame extraction. Fresh live verification completed proof `CS-2026-0007` and incident `INC-2026-0003` successfully.
- Zerops local `/tmp` media is ephemeral across redeploys. Historical incident records can therefore fail when their original media is gone; production persistence must use object storage or a persistent volume.
- Native Zerops API and worker services must use the project `storage` object store (`storage_apiUrl`, `storage_bucketName`, `storage_accessKeyId`, `storage_secretAccessKey`) so both services can read the same uploaded media after redeploys.
- Live Zerops service hostnames are `db`, `valkey`, `storage`, `api`, `worker`, and `web`; keep deployment references aligned with those names.
- FFmpeg/FFprobe resolution first uses the system PATH, then the build artifact, then a writable `/tmp/creatorshield-ffmpeg` runtime cache.

## Three-container demo deployment convention

- `zerops-3-container-import.yaml` is a demo-only infrastructure definition: `app`, `db`, and `cache` are each pinned to one container.
- `Dockerfile.zerops-3c` and `docker-compose.zerops-3c.yml` intentionally run the Next.js web server, FastAPI API, and background worker in one app container.
- The combined app uses `NEXT_PUBLIC_API_URL=/api`; `apps/web/next.config.ts` proxies `/api` and `/api/media` to the internal FastAPI listener.
- This layout uses local app storage and is not production HA. Restore separate web/API/worker services, object storage, and HA database/cache before production deployment.
## 2026-08-08 deployment consistency

- Storage initialization validates all S3 endpoint, bucket, and credential references. Literal `${...}` placeholders are treated as missing configuration and use the local storage adapter instead of crashing uploads.
- S3 uploads do not send a KMS-only `ServerSideEncryption` request because Zerops Object Storage handles encryption at the bucket level.
- The live Zerops worker is configured for 0.5–1 GB RAM; this prevents the runtime supervisor from being OOM-killed during background processing.
- Zerops worker startup must use `/bin/sh /var/www/apps/api/start-worker-zerops.sh`; Zerops executes `run.start` directly and does not interpret `cd` as a shell builtin.
- Worker media downloads retry four times with exponential backoff because private object storage may briefly lag after upload.
