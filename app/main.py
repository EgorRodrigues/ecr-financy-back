from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.accounts import router as accounts_router
from app.routers.bank_statement import router as bank_statement_router
from app.routers.categories import router as categories_router
from app.routers.contacts import router as contacts_router
from app.routers.cost_centers import router as cost_centers_router
from app.routers.credit_card_invoices import router as credit_card_invoices_router
from app.routers.credit_card_transactions import router as credit_card_transactions_router
from app.routers.dashboard import router as dashboard_router
from app.routers.expenses import router as expenses_router
from app.routers.financial_forecast import router as financial_forecast_router
from app.routers.incomes import router as incomes_router
from app.routers.subcategories import router as subcategories_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic if needed
    yield
    # Shutdown logic if needed


origins = ["*"]


app = FastAPI(title="ECR Financy API", lifespan=lifespan)


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
app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
app.include_router(
    financial_forecast_router, prefix="/financial-forecast", tags=["financial-forecast"]
)
