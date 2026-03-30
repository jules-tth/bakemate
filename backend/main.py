from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.v1.api import api_router as api_v1_router
from app.repositories.sqlite_adapter import engine, ensure_sqlite_order_schema
from app.models import __all__ as all_models
from seed import seed_data

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    ensure_sqlite_order_schema(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code here
    create_db_and_tables()
    print("Database tables created (if they didn't exist).")
    await seed_data()
    yield
    # Shutdown code here, if any

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://5173-firebase-bakemate-1757558933053.cluster-fizdampoefe4ktb4qlhma6i3ck.cloudworkstations.dev"],
    allow_credentials=True,
    allow_methods=["POST", "GET", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(api_v1_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}
