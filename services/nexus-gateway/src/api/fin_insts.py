"""
Financial Institutions API Endpoints

Reference: https://docs.nexusglobalpayments.org/apis/fin-insts

Provides lookup for PSPs, FXPs, and SAPs across the Nexus network.
Used by Source PSP to populate drop-down lists for destination selection.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Literal
from pydantic import BaseModel
from ..db import get_db

router = APIRouter(prefix="/v1", tags=["Reference Data"])


class FinancialInstitutionResponse(BaseModel):
    """Financial institution details."""
    id: str
    name: str
    bic: str
    countryCode: str
    role: str  # PSP, FXP, SAP
    isActive: bool


class FinInstListResponse(BaseModel):
    """List of financial institutions."""
    role: str
    institutions: list[FinancialInstitutionResponse]
    count: int


@router.get(
    "/fin-insts/{role}",
    response_model=FinInstListResponse,
    summary="List financial institutions by role",
    description="""
    Returns all financial institutions of a specific role across all countries.
    
    Valid roles:
    - PSP: Payment Service Providers (banks, payment apps)
    - FXP: Foreign Exchange Providers
    - SAP: Settlement Access Providers
    
    Reference: https://docs.nexusglobalpayments.org/apis/fin-insts
    """
)
async def list_fin_insts_by_role(
    role: Literal["PSP", "FXP", "SAP"],
    db: AsyncSession = Depends(get_db)
) -> FinInstListResponse:
    """
    Get all institutions of a specific role.
    
    Used to populate global selection lists.
    """
    if role == "PSP":
        query = text("""
            SELECT 
                psp_id as id, name, bic, country_code, 'PSP' as role, is_active
            FROM psps WHERE is_active = true
            ORDER BY country_code, name
        """)
    elif role == "FXP":
        query = text("""
            SELECT 
                fxp_id as id, name, '' as bic, '' as country_code, 'FXP' as role, is_active
            FROM fxps WHERE is_active = true
            ORDER BY name
        """)
    elif role == "SAP":
        query = text("""
            SELECT 
                sap_id as id, name, bic, country_code, 'SAP' as role, is_active
            FROM saps WHERE is_active = true
            ORDER BY country_code, name
        """)
    else:
        raise HTTPException(status_code=400, detail=f"Invalid role: {role}")
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    institutions = [
        FinancialInstitutionResponse(
            id=row.id,
            name=row.name,
            bic=row.bic or "",
            countryCode=row.country_code or "",
            role=row.role,
            isActive=row.is_active
        )
        for row in rows
    ]
    
    return FinInstListResponse(
        role=role,
        institutions=institutions,
        count=len(institutions)
    )


@router.get(
    "/countries/{country_code}/fin-insts/{role}",
    response_model=FinInstListResponse,
    summary="List financial institutions by country and role",
    description="""
    Returns financial institutions of a specific role within a country.
    
    This is typically used by Source PSP to populate the destination
    bank/PSP selection for the Sender.
    
    Reference: https://docs.nexusglobalpayments.org/apis/fin-insts
    """
)
async def list_fin_insts_by_country(
    country_code: str,
    role: Literal["PSP", "FXP", "SAP"],
    db: AsyncSession = Depends(get_db)
) -> FinInstListResponse:
    """
    Get institutions in a specific country.
    """
    if role == "PSP":
        query = text("""
            SELECT 
                psp_id as id, name, bic, country_code, 'PSP' as role, is_active
            FROM psps 
            WHERE country_code = :country_code AND is_active = true
            ORDER BY name
        """)
    elif role == "SAP":
        query = text("""
            SELECT 
                sap_id as id, name, bic, country_code, 'SAP' as role, is_active
            FROM saps 
            WHERE country_code = :country_code AND is_active = true
            ORDER BY name
        """)
    else:
        # FXPs are not country-specific
        raise HTTPException(
            status_code=400, 
            detail="FXPs are not country-specific. Use /fin-insts/FXP instead."
        )
    
    result = await db.execute(query, {"country_code": country_code.upper()})
    rows = result.fetchall()
    
    institutions = [
        FinancialInstitutionResponse(
            id=row.id,
            name=row.name,
            bic=row.bic,
            countryCode=row.country_code,
            role=row.role,
            isActive=row.is_active
        )
        for row in rows
    ]
    
    return FinInstListResponse(
        role=role,
        institutions=institutions,
        count=len(institutions)
    )


@router.get(
    "/fin-insts/any/{id_type}/{id_value}",
    summary="Lookup financial institution by ID",
    description="""
    Find a specific financial institution using an ID type and value.
    
    Supported ID types:
    - BICFI: BIC/SWIFT code
    - LEI: Legal Entity Identifier
    - ID: Internal Nexus ID
    
    Reference: https://docs.nexusglobalpayments.org/apis/fin-insts
    """
)
async def lookup_fin_inst(
    id_type: Literal["BICFI", "LEI", "ID"],
    id_value: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Find an institution by its identifier.
    """
    results = []
    
    if id_type == "BICFI":
        # Search PSPs and SAPs by BIC
        psp_query = text("""
            SELECT psp_id as id, name, bic, country_code, 'PSP' as role
            FROM psps WHERE UPPER(bic) = :id_value AND is_active = true
        """)
        sap_query = text("""
            SELECT sap_id as id, name, bic, country_code, 'SAP' as role
            FROM saps WHERE UPPER(bic) = :id_value AND is_active = true
        """)
        
        psp_result = await db.execute(psp_query, {"id_value": id_value.upper()})
        sap_result = await db.execute(sap_query, {"id_value": id_value.upper()})
        
        for row in psp_result.fetchall():
            results.append({
                "id": row.id,
                "name": row.name,
                "bic": row.bic,
                "countryCode": row.country_code,
                "role": row.role,
                "idType": "BICFI",
                "idValue": id_value.upper()
            })
        
        for row in sap_result.fetchall():
            results.append({
                "id": row.id,
                "name": row.name,
                "bic": row.bic,
                "countryCode": row.country_code,
                "role": row.role,
                "idType": "BICFI",
                "idValue": id_value.upper()
            })
    
    elif id_type == "ID":
        # Direct ID lookup
        psp_query = text("SELECT psp_id as id, name, bic, country_code, 'PSP' as role FROM psps WHERE psp_id = :id_value")
        fxp_query = text("SELECT fxp_id as id, name, '' as bic, '' as country_code, 'FXP' as role FROM fxps WHERE fxp_id = :id_value")
        sap_query = text("SELECT sap_id as id, name, bic, country_code, 'SAP' as role FROM saps WHERE sap_id = :id_value")
        
        for query, role in [(psp_query, "PSP"), (fxp_query, "FXP"), (sap_query, "SAP")]:
            result = await db.execute(query, {"id_value": id_value})
            row = result.fetchone()
            if row:
                results.append({
                    "id": row.id,
                    "name": row.name,
                    "bic": row.bic,
                    "countryCode": row.country_code,
                    "role": row.role,
                    "idType": "ID",
                    "idValue": id_value
                })
                break
    
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No institution found for {id_type}={id_value}"
        )
    
    return {
        "query": {"idType": id_type, "idValue": id_value},
        "results": results,
        "count": len(results)
    }
