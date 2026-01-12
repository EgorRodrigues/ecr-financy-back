import sys
import os
import argparse
from sqlalchemy import text
from app.db.postgres import get_engine, ensure_tenant_schema, metadata

def migrate_public_to_tenant(user_id: str, delete_source: bool = False):
    """
    Migrates data from public schema to a tenant schema.
    """
    # Clean user_id to match schema naming convention
    clean_user_id = user_id.replace("-", "")
    target_schema = f"tenant_{clean_user_id}"
    
    print(f"Starting migration for user {user_id} to schema {target_schema}")
    
    # Ensure tenant schema exists
    ensure_tenant_schema(target_schema)
    print(f"Schema {target_schema} ensured.")
    
    engine = get_engine()
    
    # Order matters due to foreign keys (even if loose, good practice)
    # Based on schema analysis:
    tables_order = [
        "categories",
        "cost_centers",
        "contacts",
        "accounts",
        "transactions",
        "subcategories",       # Depends on categories
        "credit_card_invoices", # Depends on accounts
        "expenses",            # Depends on various
        "incomes",             # Depends on various
        "credit_card_transactions" # Depends on invoices, etc.
    ]
    
    with engine.connect() as connection:
        # Check if tables exist in public
        # We assume they do because the app was running there
        
        for table_name in tables_order:
            print(f"Migrating table: {table_name}...")
            
            # 1. Check if public table has data
            count_query = text(f"SELECT COUNT(*) FROM public.{table_name}")
            count = connection.execute(count_query).scalar()
            
            if count == 0:
                print(f"  - No data in public.{table_name}, skipping.")
                continue
                
            print(f"  - Found {count} rows in public.{table_name}")
            
            # 2. Copy data
            # Use explicit column names to avoid order mismatch issues
            # Get columns from metadata (which matches tenant schema)
            table_obj = metadata.tables[table_name]
            columns = [c.name for c in table_obj.columns]
            columns_str = ", ".join(columns)
            
            # Use raw SQL for efficiency and simplicity
            # We explicitly map columns to ensure types align by name, not position
            copy_query = text(f"""
                INSERT INTO {target_schema}.{table_name} ({columns_str})
                SELECT {columns_str} FROM public.{table_name}
                ON CONFLICT DO NOTHING
            """)
            
            try:
                result = connection.execute(copy_query)
                connection.commit()
                print(f"  - Copied {result.rowcount} rows to {target_schema}.{table_name}")
                
                # 3. Optional: Delete from source
                if delete_source:
                    delete_query = text(f"DELETE FROM public.{table_name}")
                    connection.execute(delete_query)
                    connection.commit()
                    print(f"  - Deleted rows from public.{table_name}")
                    
            except Exception as e:
                print(f"  - Error migrating {table_name}: {e}")
                connection.rollback()
                # Stop migration on error to prevent partial state mess?
                # Or continue? Let's stop.
                raise e
                
        print("Migration completed successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate data from public schema to tenant schema.")
    parser.add_argument("user_id", help="The UUID of the user to own the data")
    parser.add_argument("--delete", action="store_true", help="Delete data from public schema after copying")
    
    args = parser.parse_args()
    
    # Need to add app to python path if running as script
    sys.path.append(os.getcwd())
    
    try:
        migrate_public_to_tenant(args.user_id, args.delete)
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)
