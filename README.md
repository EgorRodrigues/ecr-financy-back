# Financy Back

## Database Migrations (Multi-tenant)

This project uses a multi-tenant database architecture where each tenant has its own schema (e.g., `tenant_uuid`).

### Creating a New Migration

To create a new migration file, use the standard Alembic command:

```bash
poetry run alembic revision --autogenerate -m "your_migration_message"
```

### Applying Migrations to All Tenants

To apply the migrations to all tenant schemas, run the custom migration script:

```bash
poetry run python scripts/migrate_tenants.py
```

This script will:
1. Discover all schemas starting with `tenant_`
2. Apply `alembic upgrade head` to each one individually
