"""
FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.routes import equity, analyzer

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Poker Hand Analyzer & Scenario Simulator API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    equity.router,
    prefix=f"{settings.api_prefix}/equity",
    tags=["Equity"]
)

app.include_router(
    analyzer.router,
    prefix=f"{settings.api_prefix}/analyze-spot",
    tags=["GTO Analyzer"]
)


@app.get("/")
async def root():
    """Root endpoint - API health check."""
    return {
        "message": "Poker SaaS API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
