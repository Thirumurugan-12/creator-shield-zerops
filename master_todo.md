# CreatorShield Master TODO

This is the source-of-truth delivery plan for CreatorShield. It combines the original product brief, Premium UI Requirements, Product Requirements Document, and the current repository implementation.

## Status legend

- `[x]` Completed and verified
- `[~]` Partially implemented or currently in progress
- `[ ]` Planned

## Product guardrails

- [ ] CreatorShield must present technical evidence, not legal ownership decisions.
- [ ] User-provided publication information must always be labelled as user-provided.
- [ ] Do not fabricate incidents, risk scores, processing output, transcripts, analytics, or community patterns.
- [ ] Use `High suspicion`, `Critical indicators`, and `Potential pattern detected`; never claim fraud or criminal conduct.
- [ ] Every score must expose the evidence and transparent rule inputs behind it.
- [ ] Keep uploaded media private and expose it only through controlled access.

## Phase 0 — Repository and delivery foundation

### Scope

- [x] Create monorepo folders for `apps/web`, `apps/api`, `packages/shared`, and `infra`.
- [x] Add Docker Compose with separate `web` and `api` services.
- [x] Add `.env.example`, `.gitignore`, Makefile, and README setup instructions.
- [x] Add Zerops service-boundary documentation.
- [x] Add API health test and Python compilation check.
- [x] Add frontend production build.
- [ ] Add CI for frontend build, backend tests, linting, and type checking.
- [x] Add Docker healthchecks and startup dependency checks.
- [ ] Add a root-level developer seed/reset command.

### Exit criteria

- [x] `docker compose config` passes.
- [x] Backend test suite passes.
- [x] `npm run build` passes in `apps/web`.
- [ ] `docker compose up --build` runs successfully with Docker available.

## Phase 1 — Infrastructure and persistence

### Scope

- [x] Add PostgreSQL to the local Compose profile.
- [x] Add Valkey or Redis-compatible storage to the local Compose profile.
- [x] Add S3-compatible object storage configuration.
- [x] Add SQLAlchemy 2 database configuration.
- [x] Create Alembic environment and initial migrations.
- [x] Create `users` table with user ID, display name, Instagram username, email, and created timestamp.
- [x] Create `proofs` table with status, metadata, hashes, storage key, and timestamps.
- [x] Create `processing_jobs` and `processing_events` tables.
- [x] Add repository/service layers so route handlers stay thin.
- [x] Replace current in-memory proof dictionary with database persistence.
- [x] Add object-storage abstraction with local filesystem development adapter.
- [x] Add controlled temporary/signed media URL service for local storage and S3 presigned URLs.

### Exit criteria

- [x] Restarting the API does not lose proof records.
- [x] Uploaded files are not publicly listed or directly exposed by default.
- [x] A clean environment can initialize the database through migrations.

## Phase 2 — Authentication-ready application

### Scope

- [x] Add email/password or demo creator authentication using the PRD-approved demo fallback.
- [x] Add signed HTTP-only session cookie handling.
- [x] Protect authenticated application routes with a frontend auth guard.
- [x] Add user profile menu and sign-out action.
- [x] Add authentication-ready API dependency for current user.
- [x] Add ownership checks so users can only access their own proofs.
- [x] Add login, logout, and unauthorized states.

### Exit criteria

- [x] Unauthenticated users can view the landing page and login page only.
- [x] Authenticated users see only their own evidence.
- [x] Demo account works locally without requiring external services.

## Phase 3 — Premium frontend system and application shell

### Scope

- [x] Scaffold Next.js App Router, TypeScript strict mode, Tailwind CSS, TanStack Query, React Hook Form, Zod, next-themes, Sonner, and Lucide.
- [x] Add light, dark, and system theme support.
- [x] Add semantic theme variables for status and evidence states.
- [x] Add landing page hero, product preview, workflow explanation, and disclaimer.
- [x] Add responsive authenticated shell with sidebar and sticky header.
- [x] Add Dashboard, Proof Vault, Incidents, Reports, Community Intelligence, and Settings navigation routes.
- [x] Add honest coming-soon states for incomplete areas.
- [x] Replace the monolithic local UI helper with shadcn-compatible component files.
- [x] Add shared Button, Card, Badge, Input, Textarea, Progress, Skeleton, and Separator primitives with semantic styling.
- [x] Add functional mobile drawer navigation with overlay and close behavior.
- [x] Add command/search menu with keyboard shortcut and route navigation.
- [x] Add processing-job indicator from backend proof status, notifications affordance, and user menu interactions.
- [x] Add accessible labels, dialog semantics, focus-visible styles, keyboard shortcuts, and live loading status.
- [x] Add shared loading, empty, error, and retry state components.

### Exit criteria

- [x] Frontend builds in production mode.
- [x] All shell navigation works on desktop, tablet, and mobile.
- [ ] No dashboard screen contains fabricated data.
- [x] Theme switching is covered by semantic tokens and shared component styling.

## Phase 4 — Creator dashboard

### Scope

- [x] Add backend-backed Recent Proofs section.
- [x] Add Originals Secured summary.
- [x] Add Currently Processing summary.
- [x] Add Failed Proof Jobs summary placeholder.
- [x] Add Storage Used summary from uploaded file sizes.
- [x] Add Secure a Reel and Open Proof Vault quick actions.
- [x] Add recent processing activity display.
- [x] Add shadcn-compatible Table with proof icon, title, proof ID, registered date, status, duration, and open action.
- [x] Add real empty state: `Protect your first Reel`.
- [x] Add shared loading and API error states with retry.
- [x] Add actual failed-job counts from persisted proof status data.
- [ ] Ensure no unsupported incident/risk metrics appear before incident features exist.

### Exit criteria

- [x] Dashboard values come exclusively from authenticated backend data.
- [x] Empty, loading, and failure states are complete.
- [x] Recent activity is backed by persisted processing events.

## Phase 5 — Register original Reel flow

### Scope

- [x] Add Register Reel route.
- [x] Add title, Instagram username, publication date, URL, caption, and notes fields.
- [x] Add Zod + React Hook Form validation.
- [x] Add MP4, MOV, and WebM acceptance guidance.
- [x] Add 100 MB client-side limit.
- [x] Add multipart upload to FastAPI.
- [x] Implement five visible steps: Upload, Content Details, Publication Information, Review, Secure.
- [x] Add drag-and-drop upload zone.
- [x] Add video preview after selection.
- [x] Read and display filename, file size, duration, and resolution before submit.
- [x] Add replace and remove file actions.
- [x] Add review screen showing all entered details before submission.
- [x] Add backend Pydantic validation for metadata and file constraints.
- [x] Add XMLHttpRequest upload progress and cancellation handling.
- [x] Add duplicate SHA-256 upload detection and safe cleanup.

### Exit criteria

- [x] A creator can complete the entire form without console errors.
- [x] Invalid type, missing title, invalid URL, and oversized file are rejected clearly.
- [x] Successful submission redirects to the processing page with a proof ID.

## Phase 6 — Asynchronous Creator Proof processing

### Scope

- [x] Add proof ID generation.
- [x] Add private local file persistence.
- [x] Add SHA-256 generation.
- [x] Add in-process asynchronous status updates and event stream foundation.
- [x] Add polling every two seconds on the processing route.
- [x] Add a Valkey-backed proof queue and worker service, with local background fallback.
- [x] Add job lifecycle states: Queued, Processing, Secured, and Failed, with persisted job attempts.
- [x] Add retry action and retry count.
- [x] Add idempotent job execution for the latest queued/running job.
- [x] Integrate FFmpeg and ffprobe in the API image.
- [x] Extract duration, dimensions, codec, frame rate, and audio presence.
- [x] Extract one keyframe per second.
- [x] Generate perceptual image hashes with Pillow and ImageHash.
- [x] Add development audio fingerprint provider using normalized PCM SHA-256.
- [x] Add transcript provider abstraction with an explicit unavailable fallback.
- [x] Persist each processing event with timestamp and job ID.
- [x] Calculate evidence completeness from actual generated artifacts.
- [x] Add failure reason and recovery guidance.

### Required processing sequence

```text
Upload secured
→ Metadata extracted
→ File hash generated
→ Keyframes extracted
→ Audio fingerprint generated
→ Transcript generated or marked unavailable
→ Creator Proof finalised
```

### Exit criteria

- [x] Processing survives API restarts through the Valkey queue and worker.
- [x] Progress never claims an artifact exists before it is generated.
- [x] Each event in the UI maps to a persisted backend event.
- [x] A real uploaded video produces a Creator Proof record with FFmpeg metadata, keyframes, and audio/transcript status.

## Phase 7 — Proof Vault and Creator Proof details

### Proof Vault scope

- [x] Add Proof Vault route.
- [x] Add proof cards with title, proof ID, secured date, status, and completeness.
- [x] Add server-backed search query.
- [x] Add status filter.
- [x] Add date sorting and pagination-ready API.
- [x] Add table/grid view toggle.
- [x] Add loading, empty, and error states with retry.
- [ ] Add per-proof action menu.

### Proof details scope

- [x] Add proof details route.
- [x] Display proof ID, title, username, registration timestamp, publication details, file size, hash, storage status, and activity.
- [x] Display technical evidence disclaimer.
- [x] Add tabs: Overview, Keyframes, Transcript, Technical Evidence, Activity.
- [x] Add temporary signed video preview.
- [x] Add responsive keyframe gallery with timestamps and perceptual-hash status.
- [x] Add transcript panel with unavailable/no-speech state and copy action.
- [x] Add complete-hash access and copy action.
- [x] Add duration, dimensions, codec, frame rate, audio status, filename, and private storage status.
- [x] Add Create Incident action.
- [ ] Add downloadable Creator Proof record.

### Exit criteria

- [x] A creator can find, filter, open, and inspect any persisted proof.
- [x] Every visible technical field maps to a real stored artifact or explicit unavailable state.
- [x] The proof page is useful on mobile and desktop.

## Phase 8 — Incident creation and suspicious-copy intake

### Scope

- [x] Add New Incident route and five-step intake stepper.
- [x] Select a registered original.
- [x] Upload suspicious video with MP4, MOV, and WebM validation.
- [x] Add suspicious username, claimed publication date, URL, caption, and notes.
- [x] Add optional complaint-notice, payment-demand, and additional evidence file intake.
- [x] Store incident records and evidence-file inventory privately.
- [x] Add incident lifecycle foundation with Queued status and persisted intake events.
- [x] Add incident processing status page with polling and honest pending state.
- [x] Add incident ownership and access checks.

### Exit criteria

- [x] A creator can submit a suspicious copy linked to an original proof.
- [x] Optional complaint evidence is stored privately.
- [ ] Failed incident jobs can be retried without duplicating records once incident analysis workers are added.

## Phase 9 — Video comparison engine

### Visual comparison

- [x] Extract frames from original and suspicious videos.
- [x] Generate perceptual hashes for both videos.
- [x] Compare normal and horizontally mirrored versions.
- [x] Support timing tolerance through duration-aware frame matching.
- [~] Detect matching segments and matching keyframes; matching counts are persisted, while visual side-by-side keyframe evidence remains.
- [~] Attempt indicators for trim, mirrored reuse, re-encoding, and partial reuse; crop, watermark, speed, and color indicators remain.

### Audio and transcript comparison

- [ ] Implement Chromaprint, MFCC, cross-correlation, or approved audio provider.
- [x] Compare original and suspicious audio fingerprints with a deterministic local PCM fingerprint fallback.
- [~] Transcribe both videos where provider is available; local development reports transcript unavailable explicitly.
- [~] Compare transcript similarity and overlapping phrases; deferred until a transcription provider is configured.

### Output

- [x] Visual similarity percentage.
- [x] Audio similarity percentage.
- [x] Transcript similarity percentage field with an explicit unavailable state.
- [x] Timeline confidence.
- [x] Combined similarity using `visual × 45% + audio × 30% + transcript × 20% + timeline × 5%`, with unavailable transcript weight excluded and remaining weights normalized.
- [x] Matching segment count.
- [x] Matching audio duration.
- [ ] Side-by-side matching keyframes.
- [x] Modification indicators with evidence explanations for the implemented checks.

### Exit criteria

- [x] The comparison result is reproducible for the same inputs.
- [x] Individual scores and combined score are visible.
- [x] No result is shown without the evidence supporting it.

## Phase 10 — Copyright-notice analysis and suspicion score

### Complaint ingestion

- [x] Accept PNG, JPG, JPEG, and PDF complaint evidence.
- [x] Extract claimant name, email, company, URLs, publication dates, complaint date, payment amount, phone, payment ID, contacts, and requested action when text is available.
- [~] Add OCR/document parser provider abstraction; local PDF extraction is available and image OCR reports an explicit unavailable state.
- [x] Store original complaint file and extracted fields separately.

### Suspicious-language rules

- [x] Detect payment demands.
- [x] Detect withdrawal-of-complaint requests.
- [x] Detect urgent deadlines and threatening language.
- [x] Detect requests to avoid official support.
- [x] Detect requests for private communication, OTPs, or passwords.
- [x] Detect guaranteed account-restoration claims.

### Transparent score

- [x] Creator registration predates claimant publication: `+25`.
- [x] Content similarity above 85%: `+25`.
- [x] Payment demand: `+30`.
- [x] Claimant appears in multiple reports: `+15`; applied only when Phase 11 produces an explainable simulated match.
- [x] Claimed original source missing: `+10`.
- [x] Threatening or urgent language: `+10`.
- [x] Request to avoid official support: `+10`.
- [x] Cap score at 100.
- [x] Map 0–29 to Low suspicion.
- [x] Map 30–59 to Needs review.
- [x] Map 60–79 to High suspicion.
- [x] Map 80–100 to Critical indicators.

### Exit criteria

- [x] Every score component is inspectable in the UI.
- [x] The UI uses required non-accusatory wording.
- [x] Complaint analysis clearly separates extraction from interpretation.

## Phase 11 — Community intelligence

### Scope

- [x] Add simulated seeded incident data model.
- [x] Correlate claimant email, phone, username, domain, payment identifier, message fingerprint, attachment hash, and repeated wording.
- [x] Add community pattern result to incident details.
- [x] Display `Simulated community intelligence` label wherever seeded data appears.
- [x] Display count of related simulated reports, payment-demand occurrences, creator restrictions, and first recorded date.
- [x] Never present simulated reports as verified real-world findings.

### Exit criteria

- [x] Related-report matches are explainable and traceable to the correlating identifier.
- [x] Simulated data is visually and textually separated from uploaded evidence.

## Phase 12 — Evidence report generation

### Scope

- [x] Add report preview route.
- [x] Show report sections and evidence completeness.
- [x] Show missing-information warnings.
- [x] Generate downloadable PDF.
- [x] Include cover page and incident reference.
- [x] Include creator details and executive summary.
- [x] Include Creator Proof and original metadata.
- [x] Include suspicious-content metadata and timeline comparison.
- [~] Include visual, audio, transcript, and matching-keyframe evidence; transcript and side-by-side matching keyframes remain explicit unavailable states where not configured.
- [x] Include complaint extraction and suspicious indicators.
- [x] Include related simulated reports.
- [x] Include evidence file inventory, limitations, and disclaimer.
- [x] Add report status and generated timestamp.
- [x] Add report download event to activity.

### Required report limitation

```text
This report presents technical evidence only. It does not determine copyright ownership, establish unlawful conduct, or provide legal advice.
```

### Exit criteria

- [x] A completed incident can generate a readable PDF without fabricated fields.
- [x] Missing evidence is called out instead of silently omitted.
- [x] Downloaded report matches the preview and contains the required disclaimer.

## Phase 13 — Security, accessibility, and quality

### Security

- [x] Validate MIME type, extension, size, and content signature.
- [x] Prevent path traversal and unsafe filenames.
- [x] Keep object storage private.
- [x] Add malware scanning hook for uploaded files.
- [x] Add rate limits for uploads and expensive processing.
- [x] Add authorization checks to every proof, incident, media, and report endpoint.
- [x] Add safe logging without leaking file contents or sensitive complaint data.
- [x] Review CORS and production environment defaults.

### Quality

- [~] Add backend unit tests for schemas, repositories, processing, similarity, score rules, and report generation; upload-security coverage is added, broader service coverage remains.
- [ ] Add frontend tests for form validation and status states.
- [ ] Add end-to-end upload → process → proof test.
- [ ] Add end-to-end incident → compare → report test.
- [ ] Add browser smoke tests for responsive layouts.
- [ ] Add accessibility checks for keyboard navigation, labels, focus, and contrast.
- [ ] Add structured logs and error monitoring.

### Exit criteria

- [~] No critical security or authorization findings remain; full production and end-to-end review remains.
- [ ] Core vertical slices pass in a clean Docker environment.
- [ ] All important states have a test or documented manual verification.

## Phase 14 — Zerops deployment and release

### Scope

- [x] Define separate Zerops services for web, API, worker, PostgreSQL, Valkey, and object storage.
- [x] Add production environment variable documentation.
- [x] Add build and start commands for each service.
- [x] Add migration step before API rollout.
- [x] Add persistent volume/object-storage strategy.
- [x] Add health/readiness endpoints.
- [x] Add HTTPS and secure cookie configuration.
- [~] Add production logging and monitoring; deployment config documents the boundary, runtime verification remains.
- [ ] Add deployment smoke test.
- [x] Document rollback and data backup procedure.

### Exit criteria

- [ ] Zerops deployment succeeds from a clean checkout.
- [ ] A production upload can be processed into a Creator Proof.
- [ ] Logs, health checks, and persisted data are available after redeploy.

## Current repository verification

- [x] `docker compose config` passes.
- [x] `python3 -m pytest -q apps/api/tests/test_health.py` passes.
- [x] `python3 -m compileall -q apps/api/app` passes.
- [x] `npm run build` passes in `apps/web`.
- [ ] Docker Compose runtime smoke test pending because Docker daemon must be running.

## Change log

### 2026-08-07

- Expanded this file into a complete phased plan based on the original source requirements and current repository structure.
- Added explicit phases for persistence, authentication, UI shell, registration, processing, proof vault, incidents, comparison, complaint analysis, community intelligence, reporting, security, testing, and Zerops deployment.
- Preserved completed work and documented the current Docker runtime limitation.
- Completed Phase 1 persistence foundation: PostgreSQL/Valkey Compose services, SQLAlchemy models/repositories, Alembic migration, Redis/Valkey queue, worker service, and local/S3-compatible storage adapter.
- Completed signed media access with expiring HMAC URLs for local storage and presigned URLs for S3-compatible storage.
- Completed Phase 2 authentication foundation: demo login, signed HTTP-only sessions, current-user dependency, proof ownership filtering, frontend route guard, and logout flow.
- Continued Phase 3 shell work: functional mobile navigation, command palette with `⌘K`/`Ctrl+K`, real processing-job count, notification affordance, and shell sign-out interactions.
- Finished Phase 3 shared UI foundation: split shadcn-compatible primitives, shared async states, semantic focus-visible behavior, accessible status messaging, and a passing production build.
- Completed Phase 4 dashboard increment: responsive proof table, real processing/failed counts, backend-backed activity timeline, and complete loading/error/empty states.
- Completed Phase 5 registration flow: five-step form, drag-and-drop, real video preview metadata, review step, cancellable upload progress, Pydantic validation, and duplicate hash protection.
- Completed Phase 6 processing foundation: FFmpeg/ffprobe extraction, persisted job/event states, real keyframe perceptual hashes, audio fingerprint fallback, transcript-unavailable state, retry handling, failure recovery, and processing UI updates.
- Completed Phase 7 evidence library: server-backed Vault search/filter/sort, pagination-ready API, table/grid views, proof evidence tabs, signed video/keyframe previews, technical metadata, transcript fallback, hash copy, and incident entry point.
- Started Phase 8 incident intake: incident/evidence persistence, private suspicious-copy upload, ownership checks, five-step intake UI, incident list/detail routes, and honest queued-for-analysis state.
- Started Phase 9 comparison engine: incident analysis queue/worker, deterministic visual pHash comparison with mirrored-video analysis, duration-aware timeline scoring, local audio fingerprint comparison, persisted comparison outputs, modification indicators, and result UI with explicit transcript-unavailable handling.
- Started Phase 10 complaint analysis: private PNG/JPG/PDF validation, local PDF extraction provider, explicit OCR-unavailable fallback, extracted complaint fields, suspicious-language rules, transparent score indicators, score bands, and incident detail presentation separating extraction from interpretation.
- Started Phase 11 community intelligence: seeded simulated report records, explainable identifier correlation across contacts/domains/payment IDs/message fingerprints/attachment hashes/repeated wording, community counts, and clearly separated simulated-data UI with score integration.
- Started Phase 12 evidence reporting: server-backed report preview, generated PDF download, evidence-completeness warnings, shared preview/PDF context, report activity event, technical-only disclaimer, and rendered PDF visual QA.
- Started Phase 13 security and quality hardening: upload content-signature validation, safe filenames and storage keys, malware-scan hook, in-process upload/report rate limits, security headers, configurable CORS and secure cookies, and upload security tests.
- Started Phase 14 Zerops release configuration: infrastructure import manifest, separate web/API/worker deployment setups, managed PostgreSQL/Valkey/private object-storage boundaries, migration-before-rollout command, production secret mapping, secure cookie/CORS configuration, release checks, and rollback guidance.
