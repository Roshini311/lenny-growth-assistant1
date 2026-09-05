import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

@app.on_event("startup")
async def startup_event():
    logger.info("Pre-warming query embedder model on server startup...")
    try:
        from app.services.retrieval.embedder import embed_query
        embed_query("test query")
        logger.info("Query embedder model pre-warmed successfully.")
    except Exception as e:
        logger.warning(f"Query embedder pre-warming warning: {e}")


# CORS Configuration for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routes under /api prefix
app.include_router(api_router, prefix="/api")
app.include_router(chat_router)
app.include_router(essays_router)

# Mount frontend/dist static assets if built
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    async def serve_root():
        return FileResponse(os.path.join(frontend_dist, "index.html"))

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
else:
    @app.get("/")
    async def root():
        return {
            "name": "The Lenny Growth Assistant API",
            "version": "1.0.0",
            "docs_url": "/docs",
            "health_url": "/api/health"
        }

