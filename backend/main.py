import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.routers import health_router, upload_router, analyze_router

# Configure logging — DO NOT log request bodies (PDPA compliance)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def _auto_ingest_benchmarks() -> None:
    """Ingest benchmark knowledge into ChromaDB if the collection is empty.

    Runs in a background thread so it does not block app startup.
    Safe to call on every startup — upserts are idempotent.
    """
    try:
        from app.services.benchmark_rag_service import get_chroma_collection
        collection = get_chroma_collection()
        if collection is None:
            logger.warning("ChromaDB unavailable — falling back to hardcoded benchmarks.")
            return

        count = collection.count()
        if count > 0:
            logger.info(f"ChromaDB already populated ({count} chunks). Skipping auto-ingest.")
            return

        logger.info("ChromaDB collection is empty — running auto-ingest of benchmark knowledge…")
        from ingest.ingest_benchmarks import ingest
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, ingest)
        logger.info("Benchmark auto-ingest complete.")
    except Exception as exc:
        logger.error(f"Auto-ingest failed (hardcoded fallback will be used): {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(_auto_ingest_benchmarks())
    yield


app = FastAPI(
    title="InsureSight",
    description="Analyse Singapore insurance policies for gaps, over-insurance, and claim risks.",
    version="1.0.0",
    # Hide interactive docs in production to reduce attack surface
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router.router, prefix="/api", tags=["health"])
app.include_router(upload_router.router, prefix="/api", tags=["upload"])
app.include_router(analyze_router.router, prefix="/api", tags=["analyze"])


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again."},
    )
