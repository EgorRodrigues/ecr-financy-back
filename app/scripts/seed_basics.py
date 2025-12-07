from uuid import UUID
from app.core.config import settings
from app.db.cassandra import connect_cassandra, close_cassandra
from app.repositories.categories import list_categories, create_category
from app.repositories.subcategories import list_subcategories, create_subcategory
from app.models.categories import CategoryCreate
from app.models.subcategories import SubcategoryCreate
from app.repositories.cost_centers import list_cost_centers, create_cost_center
from app.models.cost_centers import CostCenterCreate


BASE_DATA: dict[str, list[str]] = {
    "Habitação": [
        "Condomínio",
        "Luz",
        "Água",
        "Gás",
        "Financiamento",
        "Internet",
        "Telefônia",
        "Diarista",
    ],
    "Alimentação": [
        "Supermercado",
        "Feira",
        "Complementos",
        "Delivery",
        "Padaria",
    ],
    "Transporte": [
        "Financiamento",
        "Seguro",
        "Estacionamento",
        "Aplicativo (Uber)",
    ],
    "Saúde/Higiêne": [
        "Farmácia",
    ],
    "Educação": [
        "Curso",
        "Livros",
    ],
    "Impostos": [
        "IPTU",
        "TCR",
        "Licenciamento",
        "IPVA",
    ],
    "Lazer": [
        "TV e Streaming",
        "Restaurante",
        "Viagens",
    ],
    "Vestuário": [],
    "Cuidados Pessoais": [
        "Barbeiro",
        "Academia",
        "Cosméticos",
    ],
    "Outros": [],
}


def _ensure_categories(session) -> dict[str, UUID]:
    existing = {c.name: c for c in list_categories(session, limit=1000)}
    ids: dict[str, UUID] = {}
    for name in BASE_DATA.keys():
        if name in existing:
            ids[name] = existing[name].id
        else:
            created = create_category(session, CategoryCreate(name=name))
            print(f"Categoria criada: {created.name} -> {created.id}")
            ids[name] = created.id
    return ids


def _ensure_subcategories(session, category_ids: dict[str, UUID]) -> None:
    for cat_name, subs in BASE_DATA.items():
        if not subs:
            continue
        cid = category_ids[cat_name]
        existing = {s.name: s for s in list_subcategories(session, cid, limit=1000)}
        for sub_name in subs:
            if sub_name in existing:
                continue
            created = create_subcategory(session, SubcategoryCreate(category_id=cid, name=sub_name))
            print(f"Subcategoria criada: {cat_name} / {created.name} -> {created.id}")


COST_CENTERS: list[str] = [
    "Casa",
    "Alimentação",
    "Transporte",
    "Saúde e Higiêne",
    "Educação",
    "Impostos e Taxas",
    "Lazer e Entretenimento",
    "Vestuário",
    "Cuidados Pessoais",
    "Outros",
]


def _ensure_cost_centers(session) -> None:
    existing = {c.name for c in list_cost_centers(session, limit=1000)}
    for name in COST_CENTERS:
        if name in existing:
            continue
        created = create_cost_center(session, CostCenterCreate(name=name))
        print(f"Centro de custo criado: {created.name} -> {created.id}")


def main() -> None:
    session = connect_cassandra(settings)
    try:
        category_ids = _ensure_categories(session)
        _ensure_subcategories(session, category_ids)
        _ensure_cost_centers(session)
        print("Seed concluído com sucesso.")
    finally:
        close_cassandra(session)


if __name__ == "__main__":
    main()
