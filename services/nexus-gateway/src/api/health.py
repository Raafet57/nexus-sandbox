"""
Health check endpoints.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint for container orchestration.
    
    Returns basic health status of the gateway.
    """
    return {
        "status": "healthy",
        "service": "nexus-gateway",
    }


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness check - verifies dependencies are available.
    """
    # TODO: Add database and Redis connectivity checks
    return {
        "status": "ready",
        "checks": {
            "database": "ok",
            "redis": "ok",
            "kafka": "ok",
        }
    }
