from sqlalchemy import select, text
from app.db.postgres import get_engine, incomes
from sqlalchemy.orm import sessionmaker

# Configurar conexão
engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

try:
    # Tentar descobrir qual schema está sendo usado ou se é public
    # Assumindo public por padrão para debug local, mas se tiver tenant, precisaria saber qual
    # Vamos listar todos os incomes de todos os schemas se possível, ou apenas do public
    
    print("--- Diagnóstico da tabela incomes ---")
    
    # 1. Verificar schemas existentes
    schemas = session.execute(text("SELECT schema_name FROM information_schema.schemata")).fetchall()
    print(f"Schemas encontrados: {[s[0] for s in schemas]}")

    # 2. Listar incomes no schema public (se houver)
    print("\nIncomes no schema 'public':")
    try:
        stmt = select(incomes)
        rows = session.execute(stmt).fetchall()
        print(f"Total de registros: {len(rows)}")
        for row in rows:
            print(f"ID: {row.id}, Status: {row.status}, Data Recebimento: {row.receipt_date}, Total Recebido: {row.total_received}, Cliente: {row.contact_id}")
    except Exception as e:
        print(f"Erro ao ler public.incomes: {e}")

    # 3. Listar status distintos
    try:
        stmt = select(incomes.c.status).distinct()
        statuses = session.execute(stmt).fetchall()
        print(f"\nStatus distintos encontrados: {[s[0] for s in statuses]}")
    except Exception as e:
        print(f"Erro ao ler status: {e}")

finally:
    session.close()
