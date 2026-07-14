from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.transfers import router as transfers_router
from app.core.exceptions import register_exception_handlers
from app.services.redis_service import redis_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_service.init_pool()
    yield
    await redis_service.close_pool()

app = FastAPI(
    title="Lynk API",
    description="Cross-device file transfer backend",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(transfers_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to Lynk API"}
