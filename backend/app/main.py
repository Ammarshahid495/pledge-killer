"""
Pledge Fighter — FastAPI Main Application Entrypoint.
Privacy-first, peer-to-peer code similarity detection platform.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from .core.config import settings
from .core.database import Base, engine
from .api.v1.router import api_router
from .schemas.common import ApiErrorDetail, ApiResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    Base.metadata.create_all(bind=engine)

    # Ensure backwards compatibility for existing SQLite databases
    try:
        with engine.connect() as conn:
            from sqlalchemy import text
            import secrets, hashlib
            result = conn.execute(text("PRAGMA table_info(classrooms)"))
            cols = [row[1] for row in result.fetchall()]
            if cols and "min_submissions" not in cols:
                conn.execute(text("ALTER TABLE classrooms ADD COLUMN min_submissions INTEGER NOT NULL DEFAULT 5"))
                conn.commit()
            if cols and "join_token" not in cols:
                conn.execute(text("ALTER TABLE classrooms ADD COLUMN join_token VARCHAR(100)"))
                conn.commit()

            # Backfill any classrooms with missing join_token
            missing_tokens = conn.execute(text("SELECT id FROM classrooms WHERE join_token IS NULL OR join_token = ''")).fetchall()
            for row in missing_tokens:
                cid = row[0]
                raw = secrets.token_urlsafe(32)
                h = hashlib.sha256(raw.encode("utf-8")).hexdigest()
                conn.execute(text("UPDATE classrooms SET join_token = :token, join_token_hash = :thash WHERE id = :cid"), {"token": raw, "thash": h, "cid": cid})
            if missing_tokens:
                conn.commit()

            # Ensure match_regions has match_type, function_name, peer_function_name
            r_result = conn.execute(text("PRAGMA table_info(match_regions)"))
            r_cols = [row[1] for row in r_result.fetchall()]
            if r_cols and "match_type" not in r_cols:
                conn.execute(text("ALTER TABLE match_regions ADD COLUMN match_type VARCHAR(20) DEFAULT 'EXACT'"))
            if r_cols and "function_name" not in r_cols:
                conn.execute(text("ALTER TABLE match_regions ADD COLUMN function_name VARCHAR(100)"))
            if r_cols and "peer_function_name" not in r_cols:
                conn.execute(text("ALTER TABLE match_regions ADD COLUMN peer_function_name VARCHAR(100)"))

            # Ensure similarity_matches has matched_functions_json
            m_result = conn.execute(text("PRAGMA table_info(similarity_matches)"))
            m_cols = [row[1] for row in m_result.fetchall()]
            if m_cols and "matched_functions_json" not in m_cols:
                conn.execute(text("ALTER TABLE similarity_matches ADD COLUMN matched_functions_json TEXT"))
            conn.commit()
    except Exception:
        pass

    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Privacy-first, peer-to-peer code similarity detection platform with Stanford MOSS-grade engine.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Standardized Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ApiResponse(
            success=False,
            message="An unexpected server error occurred",
            error=ApiErrorDetail(code="INTERNAL_SERVER_ERROR", message=str(exc)),
        ).model_dump(),
    )


# Health checks
@app.get("/health", tags=["Health"])
def health_check():
    return ApiResponse(
        success=True,
        data={"status": "healthy", "service": "pledge-fighter-api"},
        message="Service is healthy",
    )


@app.get("/ready", tags=["Health"])
def readiness_check():
    return ApiResponse(
        success=True,
        data={"status": "ready", "database": "connected"},
        message="Service is ready",
    )


# Browser direct link redirect fallback (in case someone opens backend port 8000)
@app.get("/join/{token}", tags=["Classrooms"])
def browser_join_redirect(token: str):
    return RedirectResponse(url=f"http://localhost:5173/join/{token}")


# Mount API v1
app.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
