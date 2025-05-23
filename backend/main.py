from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.v1.api import api_router as api_v1_router
from app.repositories.sqlite_adapter import engine
from app.models import __all__ as all_models

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code here
    create_db_and_tables()
    print("Database tables created (if they didn't exist).")
    yield
    # Shutdown code here, if any

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}
