"""
Financial Institutions API Endpoints

Reference: https://docs.nexusglobalpayments.org/apis/fin-insts

Provides lookup for PSPs, FXPs, and SAPs across the Nexus network.
Used by Source PSP to populate drop-down lists for destination selection.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path
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
    id_type: Literal["BICFI", "LEI", "ID"] = Path(..., alias="idType"),
    id_value: str = Path(..., alias="idValue"),
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


class FinInstRequest(BaseModel):
    """Request to create/update a financial institution."""
    bic: str
    name: str
    countryCode: str
    role: Literal["PSP", "FXP", "SAP"]
    isActive: bool = True


@router.post(
    "/fin-insts",
    summary="Register Financial Institution (Admin)",
    description="Add a new Financial Institution to the Nexus registry."
)
async def create_fin_inst(
    body: FinInstRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register a new FI."""
    # Check if duplicate BIC exists
    queries = {
        "PSP": text("SELECT 1 FROM psps WHERE bic = :bic"),
        "FXP": text("SELECT 1 FROM fxps WHERE name = :name"),  # FXPs might not have BIC in current schema, checking name
        "SAP": text("SELECT 1 FROM saps WHERE bic = :bic")
    }
    
    # Validation logic specific to roles
    check_query = queries.get(body.role)
    if check_query:
        # Note: FXP schema might check name or ID, here we check name uniqueness for FXP, BIC for others
        check_param = {"name": body.name} if body.role == "FXP" else {"bic": body.bic.upper()}
        res = await db.execute(check_query, check_param)
        if res.fetchone():
            raise HTTPException(status_code=409, detail=f"{body.role} with this identifier already exists")

    import uuid
    new_id = str(uuid.uuid4())
    
    if body.role == "PSP":
        insert_query = text("""
            INSERT INTO psps (psp_id, bic, name, country_code, is_active, fee_percent)
            VALUES (:id, :bic, :name, :country, :active, 0.0)
        """)
        await db.execute(insert_query, {
            "id": new_id, "bic": body.bic.upper(), "name": body.name, 
            "country": body.countryCode.upper(), "active": body.isActive
        })
    elif body.role == "FXP":
        insert_query = text("""
            INSERT INTO fxps (fxp_id, name, is_active, base_spread_bps)
            VALUES (:id, :name, :active, 50)
        """)
        await db.execute(insert_query, {
            "id": new_id, "name": body.name, "active": body.isActive
        })
    elif body.role == "SAP":
        insert_query = text("""
            INSERT INTO saps (sap_id, bic, name, country_code, is_active)
            VALUES (:id, :bic, :name, :country, :active)
        """)
        await db.execute(insert_query, {
            "id": new_id, "bic": body.bic.upper(), "name": body.name, 
            "country": body.countryCode.upper(), "active": body.isActive
        })
    
    await db.commit()
    
    return {
        "status": "success",
        "message": f"Registered {body.role} {body.name} ({body.bic})",
        "id": new_id
    }


@router.put(
    "/fin-insts/{fin_inst_id}",
    summary="Update Financial Institution (Admin)",
    description="Update details of an existing Financial Institution."
)
async def update_fin_inst(
    body: FinInstRequest,
    fin_inst_id: str = Path(..., alias="finInstId"),
    db: AsyncSession = Depends(get_db)
):
    """Update an FI."""
    # This assumes ID is unique across tables or user knows the role table to look in.
    # For simplicity, we try to update based on the role provided in the body.
    
    if body.role == "PSP":
        query = text("""
            UPDATE psps SET bic = :bic, name = :name, country_code = :country, is_active = :active
            WHERE psp_id = :id
        """)
    elif body.role == "FXP":
        query = text("""
            UPDATE fxps SET name = :name, is_active = :active
            WHERE fxp_id = :id
        """)
    elif body.role == "SAP":
        query = text("""
            UPDATE saps SET bic = :bic, name = :name, country_code = :country, is_active = :active
            WHERE sap_id = :id
        """)
    else:
        raise HTTPException(status_code=400, detail="Invalid Role")

    params = {
        "id": fin_inst_id,
        "bic": body.bic.upper(),
        "name": body.name,
        "country": body.countryCode.upper(),
        "active": body.isActive
    }
    # FXP table doesn't have bic/country in schema inferred from create, removing if needed or ensuring query aligns
    if body.role == "FXP":
        params = {"id": fin_inst_id, "name": body.name, "active": body.isActive}

    result = await db.execute(query, params)
    await db.commit()
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"{body.role} with ID {fin_inst_id} not found")

    return {
        "status": "success",
        "message": f"Updated {body.name} ({fin_inst_id})",
        "updatedFields": body.dict()
    }
