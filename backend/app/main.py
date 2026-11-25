import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.api_router import api_router
from app.database.session import init_db
from app.api.v1.agents import router as agents_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("querylens")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing QueryLens AI Application Database...")
    init_db()
    logger.info("Database initialized successfully.")
    yield
    logger.info("Shutting down QueryLens AI Backend...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="QueryLens AI – Multi-Database Conversational Intelligence Platform REST API",
    lifespan=lifespan,
)

# CORS configuration supporting localhost, 127.0.0.1, and subports
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers (support both /api and /api/v1 prefixes)
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(api_router, prefix="/api")

# Direct websocket mount for agents (e.g., /ws/agents/connect/{agent_token})
app.include_router(agents_router, prefix="/ws")

@app.get("/")
def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs",
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "llm_provider": settings.DEFAULT_LLM_PROVIDER,
        "allow_private_ips": settings.ALLOW_PRIVATE_IPS,
    }
