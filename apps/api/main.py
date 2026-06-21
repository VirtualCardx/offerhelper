from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.routers.candidates import router as candidate_router
from apps.api.routers.compensation_strategies import router as strategy_router
from apps.api.routers.employee_salary import router as employee_salary_router
from apps.api.routers.health import router as health_router
from apps.api.routers.market_salary import router as market_salary_router
from apps.api.routers.models import router as model_router
from apps.api.routers.offer_decision import router as offer_router
from apps.api.routers.org import router as org_router
from apps.api.routers.reports import router as report_router
from apps.api.routers.tasks import router as task_router
from src.shared.config.settings import get_settings
from src.shared.infrastructure.db.session import init_db
from src.shared.presentation.errors import register_exception_handlers


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    openapi_url=f"{settings.api_prefix}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

cors_origins = settings.allowed_cors_origins
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials="*" not in cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

register_exception_handlers(app)
app.include_router(candidate_router, prefix=settings.api_prefix)
app.include_router(strategy_router, prefix=settings.api_prefix)
app.include_router(employee_salary_router, prefix=settings.api_prefix)
app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(market_salary_router, prefix=settings.api_prefix)
app.include_router(model_router, prefix=settings.api_prefix)
app.include_router(offer_router, prefix=settings.api_prefix)
app.include_router(org_router, prefix=settings.api_prefix)
app.include_router(report_router, prefix=settings.api_prefix)
app.include_router(task_router, prefix=settings.api_prefix)
