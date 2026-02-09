import argparse
import json
import logging
import os
import sqlite3
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import MetaData, create_engine, insert, text, Boolean, Numeric, Integer, Date, DateTime
from sqlalchemy.engine import Engine
from sqlalchemy.sql import sqltypes

# Import models to ensure they are registered in Base.metadata for creation
from app.db.base import Base
import app.models  # noqa: F401

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Configuration
# Default to what user specified
OLD_DB_URL = os.getenv("OLD_DB_URL", "postgresql+psycopg://postgres:dpostgres@localhost:5432/financy_db")
NEW_DB_URL = os.getenv("NEW_DB_URL", "postgresql+psycopg://postgres:postgres@localhost:5433/financy_db")
SQLITE_DB_PATH = "legacy_dump.db"

# Tables in dependency order (Parents before Children)
TABLES_ORDER = [
    "contacts",
    "categories",
    "cost_centers",
    "subcategories",
    "accounts",
    "expenses",
    "incomes",
    "credit_card_invoices",
    "credit_card_transactions",
]

# ID Mapping: (table_name, old_id) -> new_uuid
id_mapping: dict[tuple[str, Any], uuid.UUID] = {}

# Defaults for missing required columns
DEFAULTS = {
    "contacts": {
        "type": "customer",
        "person_type": "individual",
    },
    "accounts": {
        "type": "checking",
    },
    "categories": {
        "type": "expense",  # Assumption
    },
    "credit_card_invoices": {
        "status": "open",
    },
    "credit_card_transactions": {
        "status": "pending",
    },
    "expenses": {
        "status": "pending",
        "amount": 0.0,
    },
    "incomes": {
        "status": "pending",
        "amount": 0.0,
    }
}


def get_db_engine(url: str, schema: str = None) -> Engine:
    # Set search_path to the specified schema if provided
    connect_args = {}
    if schema:
        connect_args = {'options': f'-csearch_path={schema}'}
    return create_engine(url, connect_args=connect_args)


def is_valid_uuid(val: Any) -> bool:
    if isinstance(val, uuid.UUID):
        return True
    if not isinstance(val, str):
        return False
    try:
        uuid.UUID(val)
        return True
    except ValueError:
        return False


def get_new_uuid(table_name: str, old_id: Any) -> uuid.UUID:
    """
    Returns a consistent new UUID for a given old ID.
    If old_id is already a valid UUID, returns it (cast to UUID).
    Otherwise, generates a new one and stores mapping.
    """
    key = (table_name, str(old_id))
    
    if key in id_mapping:
        return id_mapping[key]

    if is_valid_uuid(old_id):
        new_id = uuid.UUID(str(old_id))
    else:
        # Generate new UUID
        new_id = uuid.uuid4()
        logger.debug(f"Mapping {table_name}: {old_id} -> {new_id}")

    id_mapping[key] = new_id
    return new_id


def get_fk_uuid(target_table: str, old_fk_id: Any) -> uuid.UUID | None:
    """
    Resolves a Foreign Key.
    """
    if old_fk_id is None:
        return None
        
    key = (target_table, str(old_fk_id))
    if key in id_mapping:
        return id_mapping[key]
    
    # Fallback: if the FK itself is a valid UUID, maybe it refers to something we preserved
    if is_valid_uuid(old_fk_id):
        return uuid.UUID(str(old_fk_id))
        
    logger.warning(f"Missing FK mapping for {target_table} ID: {old_fk_id}. Returning None.")
    return None


def serialize_for_sqlite(val: Any) -> Any:
    """
    Prepare value for SQLite (JSON dump arrays/dicts, stringify UUIDs/dates).
    """
    if isinstance(val, (dict, list)):
        return json.dumps(val)
    if isinstance(val, (uuid.UUID, date, datetime, Decimal)):
        return str(val)
    return val


def cast_value(val: Any, col_type: Any) -> Any:
    """
    Cast value based on SQLAlchemy column type.
    """
    if val is None:
        return None
    
    # Boolean
    if isinstance(col_type, (Boolean, sqltypes.Boolean)):
        if isinstance(val, str):
            return val.lower() == 'true'
        return bool(val)
        
    # Numeric/Integer
    if isinstance(col_type, (Numeric, Integer, sqltypes.Numeric, sqltypes.Integer)):
        if val == "":
            return None
        return val  # SQLAlchemy handles string to number conversion usually
        
    # Date/DateTime
    # If val is string, we assume it's ISO format or whatever
    # SQLAlchemy usually handles 'YYYY-MM-DD' strings for Date columns
    
    return val


def extract_to_sqlite(schema: str):
    """
    Reads from Old DB and writes to SQLite.
    """
    logger.info(f"Connecting to Old DB (Schema: {schema})...")
    try:
        # Connect without forcing schema in search_path to avoid potential auth issues if schema doesn't exist yet or permissions vary
        old_engine = get_db_engine(OLD_DB_URL) 
        with old_engine.connect() as conn:
            # Init SQLite
            if os.path.exists(SQLITE_DB_PATH):
                os.remove(SQLITE_DB_PATH)
            
            sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
            sqlite_cursor = sqlite_conn.cursor()

            for table in TABLES_ORDER:
                logger.info(f"Extracting table: {table}")
                try:
                    # Select explicitly from schema
                    result = conn.execute(text(f'SELECT * FROM "{schema}"."{table}"'))
                    columns = list(result.keys())
                    
                    if not columns:
                        logger.warning(f"Table {table} is empty or has no columns.")
                        continue

                    # Create SQLite table with all TEXT columns to be safe
                    cols_def = ", ".join([f'"{col}" TEXT' for col in columns])
                    create_query = f'CREATE TABLE "{table}" ({cols_def})'
                    sqlite_cursor.execute(create_query)

                    rows = result.fetchall()
                    logger.info(f"Found {len(rows)} rows in {table}")

                    if not rows:
                        continue

                    insert_query = f'INSERT INTO "{table}" VALUES ({", ".join(["?"] * len(columns))})'
                    
                    sqlite_data = []
                    for row in rows:
                        # Convert row to list and serialize
                        sqlite_data.append([serialize_for_sqlite(val) for val in row])
                    
                    sqlite_cursor.executemany(insert_query, sqlite_data)
                    sqlite_conn.commit()
                
                except Exception as e:
                    logger.error(f"Error extracting {table}: {e}")
                    # Continue to next table? Or stop? 
            
            sqlite_conn.close()
            logger.info("Extraction complete.")

    except Exception as e:
        logger.error(f"Failed to connect or extract from Old DB: {e}")
        raise


def transform_and_load(schema: str):
    """
    Reads from SQLite, transforms IDs, writes to New DB.
    """
    logger.info(f"Connecting to New DB (Schema: {schema}) and SQLite...")
    
    new_engine = get_db_engine(NEW_DB_URL, schema)
    
    # Ensure schema exists
    with new_engine.connect() as conn:
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
        conn.commit()
        logger.info(f"Schema '{schema}' ensured.")
    
    # Create tables if they don't exist in the target schema
    # Since new_engine has search_path set to schema, create_all will use it.
    logger.info("Creating tables if not exist...")
    Base.metadata.create_all(bind=new_engine)
    
    metadata = MetaData(schema=schema)
    metadata.reflect(bind=new_engine)
    
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()

    with new_engine.begin() as pg_conn: # Transactional
        # Clear target tables first to avoid duplicates
        logger.info("Cleaning target tables...")
        for table in reversed(TABLES_ORDER):
             # When using schema reflection, keys are usually "schema.table"
             key = f"{schema}.{table}"
             if key in metadata.tables or table in metadata.tables:
                pg_conn.execute(text(f'TRUNCATE TABLE "{schema}"."{table}" CASCADE'))

        for table_name in TABLES_ORDER:
            logger.info(f"Processing {table_name}...")
            
            # Check if table exists in SQLite
            try:
                sqlite_cursor.execute(f'SELECT * FROM "{table_name}"')
            except sqlite3.OperationalError:
                logger.warning(f"Table {table_name} not found in SQLite dump. Skipping.")
                continue
                
            rows = sqlite_cursor.fetchall()
            if not rows:
                continue

            if table_name not in metadata.tables:
                # Try with schema prefix in key
                key = f"{schema}.{table_name}"
                if key not in metadata.tables:
                    logger.error(f"Table {table_name} not found in New DB schema. Skipping.")
                    continue
                pg_table = metadata.tables[key]
            else:
                pg_table = metadata.tables[table_name]
            
            records_to_insert = []
            
            for row in rows:
                row_dict = dict(row)
                new_record = {}
                
                # Handle Primary Key 'id'
                old_id = row_dict.get('id')
                if old_id:
                    new_uuid = get_new_uuid(table_name, old_id)
                    new_record['id'] = new_uuid
                
                # Process other columns
                for col_name, val in row_dict.items():
                    # Rename 'account' to 'account_id' for expenses, incomes, and credit_card_transactions
                    if col_name == 'account' and table_name in ['expenses', 'incomes', 'credit_card_transactions']:
                        col_name = 'account_id'

                    if col_name == 'id':
                        continue
                    
                    if col_name not in pg_table.columns:
                        continue
                        
                    # Handle Foreign Keys
                    if col_name.endswith('_id') and val is not None:
                        # Infer target table from column name
                        target = None
                        if col_name == 'account_id': target = 'accounts'
                        elif col_name == 'category_id': target = 'categories'
                        elif col_name == 'subcategory_id': target = 'subcategories'
                        elif col_name == 'contact_id': target = 'contacts'
                        elif col_name == 'cost_center_id': target = 'cost_centers'
                        elif col_name == 'invoice_id': target = 'credit_card_invoices'
                        elif col_name == 'expense_id': target = 'expenses'
                        elif col_name == 'income_id': target = 'incomes'
                        
                        if target:
                            new_fk = get_fk_uuid(target, val)
                            new_record[col_name] = new_fk
                        else:
                            if is_valid_uuid(val):
                                new_record[col_name] = uuid.UUID(str(val))
                            else:
                                new_record[col_name] = val
                    
                    else:
                        # Regular column
                        if val is not None and (val.startswith('[') or val.startswith('{')):
                            try:
                                new_record[col_name] = json.loads(val)
                            except:
                                new_record[col_name] = val
                        else:
                            col_type = pg_table.columns[col_name].type
                            new_record[col_name] = cast_value(val, col_type)

                # Apply defaults for missing columns
                for col in pg_table.columns:
                    col_name = col.name
                    if col_name not in new_record:
                        if table_name in DEFAULTS and col_name in DEFAULTS[table_name]:
                            new_record[col_name] = DEFAULTS[table_name][col_name]

                # Remove keys that don't exist in new table (if any)
                final_record = {k: v for k, v in new_record.items() if k in pg_table.columns}
                records_to_insert.append(final_record)

            if records_to_insert:
                # Chunk inserts
                chunk_size = 1000
                for i in range(0, len(records_to_insert), chunk_size):
                    chunk = records_to_insert[i:i+chunk_size]
                    pg_conn.execute(insert(pg_table), chunk)
                logger.info(f"Inserted {len(records_to_insert)} rows into {table_name}")

    logger.info("Migration complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate data from legacy DB to new DB with schema support.")
    parser.add_argument("--schema", help="Schema name for source and target DB", default=None)
    args = parser.parse_args()

    schema = args.schema
    
    # Interactive fallback
    if not schema:
        try:
            schema = input("Please enter the schema name (e.g., 'public' or 'tenant_1'): ").strip()
        except EOFError:
            pass

    if not schema:
        logger.error("Schema name is required. Use --schema argument or provide input.")
        exit(1)

    try:
        logger.info(f"Starting migration for schema: {schema}")
        logger.info(f"Old DB: {OLD_DB_URL}")
        logger.info(f"New DB: {NEW_DB_URL}")
        
        extract_to_sqlite(schema)
        transform_and_load(schema)
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        exit(1)
