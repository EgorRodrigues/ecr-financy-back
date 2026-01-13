from datetime import date
from app.models.reporting import IncomeByCustomer
from app.repositories.reports_incomes import get_incomes_by_customer
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
from app.db.postgres import incomes, contacts, get_engine
from uuid import uuid4

# Setup
engine = get_engine()
Session = sessionmaker(bind=engine)
session = Session()

try:
    # Cleanup prévio para evitar sujeira
    session.execute(text("DELETE FROM incomes WHERE description = 'Teste Repro'"))
    session.commit()

    cid = uuid4()
    session.execute(
        contacts.insert().values(
            id=cid,
            name="Cliente Teste Repro",
            type="cliente",
            person_type="fisica",
            active=True
        )
    )
    
    # Inserir income com receipt_date NULL mas due_date hoje
    today = date.today()
    session.execute(
        incomes.insert().values(
            id=uuid4(),
            amount=100.0,
            status="recebido",
            receipt_date=None,
            due_date=today, # Fallback date
            issue_date=today,
            contact_id=str(cid),
            description="Teste Repro",
            active=True
        )
    )
    session.commit()
    
    # Teste 1: Sem filtros de data
    print("\n--- Teste 1: Sem filtros ---")
    results = get_incomes_by_customer(session, None, None)
    print(f"Resultados encontrados: {len(results)}")
    
    # Teste 2: Com filtro de data (deve pegar via due_date)
    print("\n--- Teste 2: Com filtro de data (hoje) ---")
    results_filtered = get_incomes_by_customer(session, today, today)
    print(f"Resultados encontrados: {len(results_filtered)}")
    found = False
    for r in results_filtered:
        if r.contact_name == "Cliente Teste Repro":
            print(f"-> SUCESSO: Encontrou cliente via fallback de data: {r}")
            found = True
    
    if not found:
        print("-> FALHA: Não encontrou o registro com filtro de data.")

finally:
    # Cleanup
    session.execute(text("DELETE FROM incomes WHERE description = 'Teste Repro'"))
    session.execute(text(f"DELETE FROM contacts WHERE id = '{cid}'"))
    session.commit()
    session.close()
