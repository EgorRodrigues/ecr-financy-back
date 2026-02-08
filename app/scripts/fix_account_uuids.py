import logging
from uuid import UUID

from sqlalchemy import text
from app.core.config import settings
from app.db.postgres import connect_postgres

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_valid_uuid(val):
    if val is None:
        return False
    try:
        UUID(str(val))
        return True
    except ValueError:
        return False

def get_tenant_schemas(session):
    schemas = session.execute(
        text(
            "SELECT schema_name FROM information_schema.schemata "
            "WHERE schema_name LIKE 'tenant_%'"
        )
    ).scalars().all()
    return list(schemas)

def fix_schema(session, schema_name):
    logger.info(f"--- Processing schema: {schema_name} ---")
    
    # Set search path
    session.execute(text(f"SET search_path TO {schema_name}"))
    
    # 1. Load map of Account Name -> Account ID
    try:
        accounts_result = session.execute(text("SELECT id, name FROM accounts"))
        account_map = {row.name: str(row.id) for row in accounts_result}
        logger.info(f"Loaded {len(account_map)} accounts for schema {schema_name}.")
    except Exception as e:
        logger.warning(f"Could not load accounts for schema {schema_name} (maybe table missing?): {e}")
        return

    # 2. Fix Incomes
    _fix_table(session, "incomes", account_map)

    # 3. Fix Expenses
    _fix_table(session, "expenses", account_map)

def _fix_table(session, table_name, account_map):
    logger.info(f"Checking {table_name}...")
    try:
        # We select id and account. 
        # casting to text to ensure we get a string even if it is UUID type (though if it is UUID type, it won't have invalid values)
        rows = session.execute(text(f"SELECT id, account::text FROM {table_name} WHERE account IS NOT NULL"))
        
        fixed_count = 0
        failed_count = 0
        
        for row in rows:
            row_id = row.id
            account_val = row.account
            
            if not is_valid_uuid(account_val):
                # It's a name
                if account_val in account_map:
                    new_uuid = account_map[account_val]
                    logger.info(f"Fixing {table_name} {row_id}: '{account_val}' -> {new_uuid}")
                    
                    # Update
                    # Note: We must cast :uuid to UUID if the column is UUID, or leave it as string if it is Text.
                    # Since we suspect it is Text (otherwise it wouldn't have names), passing string is fine.
                    # If it's a mix (somehow?), Postgres handles string-to-uuid cast automatically if the column is UUID.
                    # But if the column IS Text, we just write the UUID string.
                    session.execute(
                        text(f"UPDATE {table_name} SET account = :uuid WHERE id = :id"),
                        {"uuid": new_uuid, "id": row_id}
                    )
                    fixed_count += 1
                else:
                    logger.warning(f"{table_name} {row_id} has unknown account name: '{account_val}'")
                    failed_count += 1
        
        logger.info(f"{table_name}: Fixed {fixed_count}, Failed (unknown account) {failed_count}")

    except Exception as e:
        logger.error(f"Error checking/fixing {table_name}: {e}")

def main():
    SessionLocal = connect_postgres(settings)
    session = SessionLocal()
    
    try:
        # Get schemas
        schemas = get_tenant_schemas(session)
        # Add public schema as well
        schemas.append("public")
        
        if not schemas:
            logger.warning("No schemas found to process.")
        
        for schema in schemas:
            try:
                fix_schema(session, schema)
                session.commit()
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to process schema {schema}: {e}")
                
    finally:
        session.close()

if __name__ == "__main__":
    main()
