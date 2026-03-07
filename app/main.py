from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.routers.management.accounts import router as accounts_router
from app.routers.reports.bank_statement import router as bank_statement_router
from app.routers.management.categories import router as categories_router
from app.routers.management.contacts import router as contacts_router
from app.routers.management.cost_centers import router as cost_centers_router
from app.routers.management.credit_card_invoices import router as credit_card_invoices_router
from app.routers.management.credit_card_transactions import router as credit_card_transactions_router
from app.routers.management.expenses import router as expenses_router
from app.routers.reports.financial_forecast import router as financial_forecast_router
from app.routers.management.incomes import router as incomes_router
from app.routers.management.subcategories import router as subcategories_router
from app.routers.management.transfers import router as transfers_router
from app.routers.reports.dashboard import router as dashboard_router
from app.routers.management.reconciliation import router as reconciliation_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic if needed
    yield
    # Shutdown logic if needed


origins = ["*"]


app = FastAPI(title="ECR Financy API", lifespan=lifespan)


app.add_middleware(
    ProxyHeadersMiddleware,
    trusted_hosts=["*"],  # Trust all proxies (safe if behind a controlled load balancer/proxy)
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


app.include_router(categories_router, prefix="/categories", tags=["categories"])
app.include_router(subcategories_router, prefix="/subcategories", tags=["subcategories"])
app.include_router(cost_centers_router, prefix="/cost-centers", tags=["cost_centers"])
app.include_router(contacts_router, prefix="/contacts", tags=["contacts"])
app.include_router(expenses_router, prefix="/expenses", tags=["expenses"])
app.include_router(
    credit_card_transactions_router,
    prefix="/credit-card-transactions",
    tags=["credit-card-transactions"],
)
app.include_router(
    credit_card_invoices_router,
    prefix="/credit-card-invoices",
    tags=["credit-card-invoices"],
)
app.include_router(incomes_router, prefix="/incomes", tags=["incomes"])
app.include_router(accounts_router, prefix="/accounts", tags=["accounts"])
app.include_router(bank_statement_router, prefix="/bank-statement", tags=["bank-statement"])
app.include_router(
    financial_forecast_router, prefix="/financial-forecast", tags=["financial-forecast"]
)
app.include_router(transfers_router, prefix="/transfers", tags=["transfers"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
app.include_router(reconciliation_router, prefix="/reconciliation", tags=["reconciliation"])
