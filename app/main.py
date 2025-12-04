from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.db.cassandra import connect_cassandra, close_cassandra
from app.routers.health import router as health_router
from app.routers.transactions import router as transactions_router
from app.routers.categories import router as categories_router
from app.routers.subcategories import router as subcategories_router
from app.routers.cost_centers import router as cost_centers_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    session = connect_cassandra(settings)
    app.state.cassandra_session = session
    yield
    close_cassandra(app.state.cassandra_session)


app = FastAPI(title="ECR Financy API", lifespan=lifespan)
app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(transactions_router, prefix="/transactions", tags=["transactions"])
app.include_router(categories_router, prefix="/categories", tags=["categories"])
app.include_router(subcategories_router, prefix="/subcategories", tags=["subcategories"])
app.include_router(cost_centers_router, prefix="/cost-centers", tags=["cost_centers"])
