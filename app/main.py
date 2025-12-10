from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.postgres import connect_postgres, close_postgres
from app.routers.health import router as health_router
from app.routers.transactions import router as transactions_router
from app.routers.categories import router as categories_router
from app.routers.subcategories import router as subcategories_router
from app.routers.cost_centers import router as cost_centers_router
from app.routers.contacts import router as contacts_router
from app.routers.expenses import router as expenses_router
from app.routers.incomes import router as incomes_router
from app.routers.accounts import router as accounts_router
from app.routers.dashboard import router as dashboard_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    session = connect_postgres(settings)
    app.state.cassandra_session = session
    yield
    close_postgres(app.state.cassandra_session)


origins = ['*']


app = FastAPI(title="ECR Financy API", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=['*'],
    allow_headers=['*'],
    allow_credentials=True,
)


app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(transactions_router, prefix="/transactions", tags=["transactions"])
app.include_router(categories_router, prefix="/categories", tags=["categories"])
app.include_router(subcategories_router, prefix="/subcategories", tags=["subcategories"])
app.include_router(cost_centers_router, prefix="/cost-centers", tags=["cost_centers"])
app.include_router(contacts_router, prefix="/contacts", tags=["contacts"])
app.include_router(expenses_router, prefix="/expenses", tags=["expenses"])
app.include_router(incomes_router, prefix="/incomes", tags=["incomes"])
app.include_router(accounts_router, prefix="/accounts", tags=["accounts"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
