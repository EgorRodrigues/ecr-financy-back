from sqlalchemy import text

from app.db.postgres import get_engine


def migrate() -> None:
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
        print("Tenant schemas encontrados:", schemas)
        for schema in schemas:
            print(f"Atualizando schema {schema}...")
            statements = [
                (
                    "ALTER TABLE "
                    f"{schema}.credit_card_invoices "
                    "ADD COLUMN IF NOT EXISTS payment_date DATE"
                ),
                (
                    "ALTER TABLE "
                    f"{schema}.credit_card_invoices "
                    "ADD COLUMN IF NOT EXISTS interest NUMERIC(18, 2)"
                ),
                (
                    "ALTER TABLE "
                    f"{schema}.credit_card_invoices "
                    "ADD COLUMN IF NOT EXISTS fine NUMERIC(18, 2)"
                ),
                (
                    "ALTER TABLE "
                    f"{schema}.credit_card_invoices "
                    "ADD COLUMN IF NOT EXISTS discount NUMERIC(18, 2)"
                ),
                (
                    "ALTER TABLE "
                    f"{schema}.credit_card_invoices "
                    "ADD COLUMN IF NOT EXISTS total_paid NUMERIC(18, 2)"
                ),
            ]
            for stmt in statements:
                print("  Executando:", stmt)
                conn.execute(text(stmt))
        conn.commit()


def main() -> None:
    migrate()


if __name__ == "__main__":
    main()
