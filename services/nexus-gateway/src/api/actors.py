"""
Actors API - Plug-and-Play Participant Registry

Reference: Nexus Global Payments Sandbox - Actor Integration
Reference: NotebookLM 2026-02-03 - Actor Connectivity Models

This module provides a registry for sandbox participants to register their
callback URLs for real-time ISO 20022 message routing.

Actors:
- FXP: Foreign Exchange Provider (Direct to Nexus)
- IPS: Instant Payment System Operator (Direct to Nexus)
- PSP: Payment Service Provider (Indirect via IPS)
- SAP: Settlement Access Provider (Indirect via IPS)
- PDO: Proxy Directory Operator (Indirect via IPS)

Assumption A25: Actors can self-register their callback_url for sandbox testing.
Assumption A26: BIC is used as the unique identifier for actors.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Literal
from datetime import datetime, timezone
import uuid
import re
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from .callbacks import test_callback_endpoint

router = APIRouter(prefix="/v1/actors", tags=["Actor Registry"])

from .schemas import ActorRegistration, Actor, ActorsListResponse

# =============================================================================
# Models
# =============================================================================

ActorType = Literal["FXP", "IPS", "PSP", "SAP", "PDO"]

# =============================================================================
# BIC Validation
# =============================================================================

def validate_bic(bic: str) -> bool:
    """
    Validate BIC (SWIFT code) format per ISO 9362.
    
    Format: 4 letters (institution) + 2 letters (country) + 2 letters/digits (location) 
            + optional 3 letters/digits (branch, default 'XXX')
    
    Args:
        bic: BIC code to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not bic:
        return False
    
    bic = bic.upper().strip()
    
    # Must be 8 or 11 characters
    if len(bic) not in (8, 11):
        return False
    
    # First 4 characters: institution code (letters only)
    if not re.match(r'^[A-Z]{4}', bic):
        return False
    
    # Next 2 characters: country code (letters only)
    if not re.match(r'^[A-Z]{4}[A-Z]{2}', bic):
        return False
    
    # Next 2 characters: location code (letters or digits)
    if not re.match(r'^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}', bic):
        return False
    
    # If 11 characters, last 3 must be letters or digits
    if len(bic) == 11:
        if not re.match(r'^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}[A-Z0-9]{3}$', bic):
            return False
    
    return True


# =============================================================================
# Callback Test Response Model
# =============================================================================

class CallbackTestResponse(BaseModel):
    """Response from callback endpoint test."""
    success: bool
    bic: str
    callback_url: Optional[str] = Field(None, alias="callbackUrl")
    status_code: Optional[int] = Field(None, alias="statusCode")
    latency_ms: Optional[float] = Field(None, alias="latencyMs")
    error: Optional[str] = None
    error_type: Optional[str] = Field(None, alias="errorType")
    message: str
    
    class Config:
        populate_by_name = True

# =============================================================================
# In-Memory Registry (Sandbox Simplification)
# =============================================================================
# Assumption A27: Sandbox uses in-memory registry for actor data.
# Production would use a persistent database table.

_actor_registry: dict[str, dict] = {
    # Pre-seeded actors for sandbox
    "DBSSSGSG": {
        "actorId": "actor-dbs-sg",
        "bic": "DBSSSGSG",
        "actorType": "PSP",
        "name": "DBS Bank Singapore",
        "countryCode": "SG",
        "callbackUrl": None,
        "registeredAt": "2026-01-01T00:00:00.000Z",
        "status": "ACTIVE"
    },
    "KASITHBK": {
        "actorId": "actor-kasikorn-bank",
        "bic": "KASITHBK",
        "actorType": "PSP",
        "name": "Kasikorn Bank Thailand",
        "countryCode": "TH",
        "callbackUrl": None,
        "registeredAt": "2026-01-01T00:00:00.000Z",
        "status": "ACTIVE"
    },
    "MABORKKL": {
        "actorId": "actor-maybank-my",
        "bic": "MABORKKL",
        "actorType": "PSP",
        "name": "Maybank Malaysia",
        "countryCode": "MY",
        "callbackUrl": None,
        "registeredAt": "2026-01-01T00:00:00.000Z",
        "status": "ACTIVE"
    },
    "FXP-ABC": {
        "actorId": "actor-fxp-alpha",
        "bic": "FXP-ABC",
        "actorType": "FXP",
        "name": "ABC Currency Exchange",
        "countryCode": "SG",
        "callbackUrl": None,
        "registeredAt": "2026-01-01T00:00:00.000Z",
        "status": "ACTIVE"
    },
    "SGIPSOPS": {
        "actorId": "actor-sg-ips",
        "bic": "SGIPSOPS",
        "actorType": "IPS",
        "name": "Singapore FAST IPS",
        "countryCode": "SG",
        "callbackUrl": None,
        "registeredAt": "2026-01-01T00:00:00.000Z",
        "status": "ACTIVE"
    },
    "THIPSOPS": {
        "actorId": "actor-th-ips",
        "bic": "THIPSOPS",
        "actorType": "IPS",
        "name": "Thailand PromptPay IPS",
        "countryCode": "TH",
        "callbackUrl": None,
        "registeredAt": "2026-01-01T00:00:00.000Z",
        "status": "ACTIVE"
    },
}

# =============================================================================
# Endpoints
# =============================================================================

@router.post(
    "/register",
    response_model=Actor,
    summary="Register a new actor for sandbox testing",
    description="""
    Register a sandbox participant (FXP, IPS, PSP, SAP, or PDO) with an optional
    callback URL for receiving ISO 20022 messages.
    
    **Direct Participants (FXP, IPS):** Will receive messages directly from Nexus.
    **Indirect Participants (PSP, SAP, PDO):** Should configure their domestic IPS
    callback for realistic testing.
    
    **BIC Validation:** BIC must be 8 or 11 characters in ISO 9362 format.
    """,
)
async def register_actor(request: ActorRegistration):
    """Register a new actor in the sandbox."""
    # Validate BIC format
    if not validate_bic(request.bic):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid BIC format: {request.bic}. Must be 8 or 11 characters (AAAA BB CC [DDD])"
        )
    
    bic_upper = request.bic.upper().strip()
    
    if bic_upper in _actor_registry:
        raise HTTPException(status_code=409, detail=f"Actor with BIC {request.bic} already exists")
    
    # Validate actor type
    valid_types = ["FXP", "IPS", "PSP", "SAP", "PDO"]
    if request.actor_type.upper() not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid actor_type: {request.actor_type}. Must be one of: {', '.join(valid_types)}"
        )
    
    actor_id = f"actor-{uuid.uuid4().hex[:8]}"
    registered_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    actor_data = {
        "actorId": actor_id,
        "bic": bic_upper,
        "actorType": request.actor_type.upper(),
        "name": request.name,
        "countryCode": request.country_code.upper(),
        "callbackUrl": str(request.callback_url) if request.callback_url else None,
        "registeredAt": registered_at,
        "status": "ACTIVE",
        "supportedCurrencies": request.supported_currencies if request.supported_currencies else []
    }
    
    _actor_registry[bic_upper] = actor_data
    
    return Actor(**actor_data)


@router.get(
    "",
    response_model=ActorsListResponse,
    summary="List all registered actors",
    description="Retrieve a list of all sandbox participants.",
)
async def list_actors(actor_type: Optional[ActorType] = None, country_code: Optional[str] = None):
    """List registered actors with optional filtering."""
    actors = list(_actor_registry.values())
    
    if actor_type:
        actors = [a for a in actors if a["actorType"] == actor_type]
    if country_code:
        actors = [a for a in actors if a["countryCode"] == country_code.upper()]
    
    actor_list = [Actor(**a) for a in actors]
    return {"actors": actor_list, "total": len(actor_list)}


@router.get(
    "/{bic}",
    response_model=Actor,
    summary="Get actor by BIC",
    description="Retrieve details of a specific actor by their BIC code.",
)
async def get_actor(bic: str):
    """Get a specific actor by BIC."""
    actor = _actor_registry.get(bic.upper())
    if not actor:
        raise HTTPException(status_code=404, detail=f"Actor with BIC {bic} not found")
    return Actor(**actor)


@router.patch(
    "/{bic}/callback",
    response_model=Actor,
    summary="Update actor callback URL",
    description="Update the callback URL for an existing actor.",
)
async def update_callback(bic: str, callback_url: Optional[HttpUrl] = None):
    """Update the callback URL for an actor."""
    actor = _actor_registry.get(bic.upper())
    if not actor:
        raise HTTPException(status_code=404, detail=f"Actor with BIC {bic} not found")
    
    actor["callbackUrl"] = str(callback_url) if callback_url else None
    return Actor(**actor)


@router.delete(
    "/{bic}",
    summary="Deregister an actor",
    description="Remove an actor from the sandbox registry.",
)
async def deregister_actor(bic: str):
    """Remove an actor from the registry."""
    if bic.upper() not in _actor_registry:
        raise HTTPException(status_code=404, detail=f"Actor with BIC {bic} not found")
    
    del _actor_registry[bic.upper()]
    return {"message": f"Actor {bic} deregistered successfully"}


@router.post(
    "/{bic}/callback-test",
    response_model=CallbackTestResponse,
    summary="Test actor callback endpoint",
    description="""
    Send a test ping to the actor's registered callback URL.
    
    This verifies that:
    - The callback URL is reachable
    - The endpoint responds within timeout
    - HMAC signature verification works (if implemented by actor)
    
    Returns detailed diagnostic information about the test result.
    """,
)
async def test_actor_callback(bic: str):
    """Test the callback endpoint for a registered actor."""
    actor = _actor_registry.get(bic.upper())
    if not actor:
        raise HTTPException(status_code=404, detail=f"Actor with BIC {bic} not found")
    
    callback_url = actor.get("callbackUrl")
    if not callback_url:
        raise HTTPException(
            status_code=422, 
            detail=f"Actor {bic} has no callback URL configured"
        )
    
    # Run the test
    result = await test_callback_endpoint(callback_url)
    
    return CallbackTestResponse(
        success=result["success"],
        bic=bic.upper(),
        callback_url=callback_url,
        status_code=result.get("statusCode"),
        latency_ms=result.get("latencyMs"),
        error=result.get("error"),
        error_type=result.get("errorType"),
        message="Callback test successful" if result["success"] else "Callback test failed"
    )
