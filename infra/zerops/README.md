# Zerops deployment

CreatorShield has two Zerops configuration files:

- `/zerops-import.yaml` provisions the `web`, `api`, `worker`, PostgreSQL, Valkey, and private object-storage services.
- `/zerops.yaml` defines build, migration, runtime, environment, and port behavior for the three application services.

## Provision services

Install and authenticate the Zerops CLI, review the service sizes and secret policy, then import the infrastructure manifest:

```bash
zcli project project-import zerops-import.yaml
```

The exact CLI project/service flags depend on the Zerops project selected in the dashboard. The service hostnames must remain `web`, `api`, `worker`, `db`, `cache`, and `storage` because they are the deployment boundary documented here.

## Configure secrets and bindings

Before the first push, configure these environment variables in the API and worker services. Use the managed service connection values from Zerops rather than committing them to Git:

```text
CREATORSHIELD_DATABASE_URL=postgresql+psycopg://...
CREATORSHIELD_REDIS_URL=rediss://...
CREATORSHIELD_S3_ENDPOINT_URL=https://...
CREATORSHIELD_S3_BUCKET=...
CREATORSHIELD_S3_ACCESS_KEY_ID=...
CREATORSHIELD_S3_SECRET_ACCESS_KEY=...
CREATORSHIELD_MEDIA_SIGNING_SECRET=<long random value>
CREATORSHIELD_SESSION_SECRET=<long random value>
CREATORSHIELD_WEB_URL=https://<web public host>
CREATORSHIELD_API_URL=https://<api public host>
```

`zerops.yaml` maps these deployment variables into the application’s expected `DATABASE_URL`, `REDIS_URL`, S3, signing-secret, cookie, and CORS settings. `SECURE_COOKIES=true` is set for the API and worker runtime configuration.

## Deploy

Push each application setup from the repository root:

```bash
zcli service push --setup api
zcli service push --setup worker
zcli service push --setup web
```

The API runs `alembic upgrade head` during initialization before starting Uvicorn. The worker shares the API code and managed PostgreSQL, Valkey, and object-storage bindings. The API exposes `/health` on port `8000`; the web service exposes port `3000`.

## Release checks

1. Verify `/health` returns `{"status":"ok"}`.
2. Confirm the API can create a secure session with an HTTPS-only cookie.
3. Register a small MP4 and confirm the worker persists metadata and evidence.
4. Create an incident and confirm the comparison worker and report download event.
5. Confirm uploaded objects are private and only signed URLs resolve.
6. Record the deployed version and migration revision for rollback.

The first real Zerops deployment remains an environment-dependent operation: it requires an authenticated Zerops project, service provisioning, configured secrets, and public hostnames.
