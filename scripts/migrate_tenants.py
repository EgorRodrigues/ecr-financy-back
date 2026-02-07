import os
import subprocess
import sys
from sqlalchemy import text
from app.db.postgres import get_engine

def get_tenant_schemas():
    engine = get_engine()
    with engine.connect() as conn:
        schemas = [
            row[0]
            for row in conn.execute(
                text(
                    "SELECT schema_name FROM information_schema.schemata "
                    "WHERE schema_name LIKE 'tenant_%'"
                )
            )
        ]
    return schemas

def run_migrations(schema_name):
    print(f"Applying migrations for schema: {schema_name}")
    
    env = os.environ.copy()
    env["TARGET_SCHEMA"] = schema_name
    
    try:
        # Run alembic upgrade head
        subprocess.run(
            ["poetry", "run", "alembic", "upgrade", "head"],
            env=env,
            check=True,
            capture_output=False
        )
        print(f"Successfully migrated schema: {schema_name}")
    except subprocess.CalledProcessError as e:
        print(f"Error migrating schema {schema_name}: {e}")
        # Decide if we want to stop or continue. Usually stop to fix issues.
        sys.exit(1)

def main():
    schemas = get_tenant_schemas()
    
    # Optionally migrate public schema first if needed
    # run_migrations("public")
    
    if not schemas:
        print("No tenant schemas found.")
        return

    print(f"Found {len(schemas)} tenant schemas: {schemas}")
    
    for schema in schemas:
        run_migrations(schema)
    
    print("All tenant migrations completed successfully.")

if __name__ == "__main__":
    main()
