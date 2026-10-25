from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.config import settings

app = FastAPI(
    title="Document Copilot API",
    description="Backend service for Driftwood Capital Document Copilot",
    version="0.1.0",
)

# CORS middleware for browser frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint to verify service availability and config."""
    return {
        "status": "ok",
        "environment": settings.environment,
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000)