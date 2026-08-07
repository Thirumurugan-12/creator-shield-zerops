# Zerops deployment

The `api` and `web` services are intentionally isolated in Docker Compose so they can be mapped to separate Zerops services. Replace the local SQLite/private volume configuration with PostgreSQL, Valkey, and S3-compatible storage bindings for production.
