import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import router as api_router
from app.api.chat import router as chat_router
from app.api.essays import router as essays_router

# Configure structured logging foundation
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("lenny_assistant")

app = FastAPI(
    title="The Lenny Growth Assistant API",
    description="Backend API for Lenny's Podcast transcript RAG knowledge assistant",
    version="1.0.0"
)

# CORS Configuration for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routes under /api prefix
app.include_router(api_router, prefix="/api")
app.include_router(chat_router)
app.include_router(essays_router)


@app.get("/")
async def root():
    return {
        "name": "The Lenny Growth Assistant API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_url": "/api/health"
    }
