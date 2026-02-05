import uuid
import random
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import Base, engine, get_db, async_session
from src.models import Country, Quote, Payment, Actor, FXRate
from src.config import settings

SEED_DATA = {
    "countries": [
        {"code": "SG", "name": "Singapore", "currency_code": "SGD", "max_amount": 200000, "ips_name": "FAST"},
        {"code": "TH", "name": "Thailand", "currency_code": "THB", "max_amount": 2000000, "ips_name": "PromptPay"},
        {"code": "MY", "name": "Malaysia", "currency_code": "MYR", "max_amount": 50000, "ips_name": "DuitNow"},
        {"code": "PH", "name": "Philippines", "currency_code": "PHP", "max_amount": 500000, "ips_name": "InstaPay"},
        {"code": "ID", "name": "Indonesia", "currency_code": "IDR", "max_amount": 100000000, "ips_name": "BI-FAST"},
        {"code": "IN", "name": "India", "currency_code": "INR", "max_amount": 1000000, "ips_name": "UPI"},
    ],
    "actors": [
        {"bic": "DBSSSGSG", "name": "DBS Bank", "actor_type": "PSP", "country_code": "SG", "status": "ACTIVE"},
        {"bic": "OCBCSGSG", "name": "OCBC Bank", "actor_type": "PSP", "country_code": "SG", "status": "ACTIVE"},
        {"bic": "ULOVIEMOVE", "name": "Grab Financial", "actor_type": "PSP", "country_code": "SG", "status": "ACTIVE"},
        {"bic": "BKKBTHBK", "name": "Bangkok Bank", "actor_type": "PSP", "country_code": "TH", "status": "ACTIVE"},
        {"bic": "KASITHBK", "name": "Kasikorn Bank", "actor_type": "PSP", "country_code": "TH", "status": "ACTIVE"},
        {"bic": "MAYBMYKL", "name": "Maybank", "actor_type": "PSP", "country_code": "MY", "status": "ACTIVE"},
        {"bic": "FAST001", "name": "FAST Singapore", "actor_type": "IPS", "country_code": "SG", "status": "ACTIVE"},
        {"bic": "PPAY001", "name": "PromptPay Thailand", "actor_type": "IPS", "country_code": "TH", "status": "ACTIVE"},
        {"bic": "NEXUSFXP", "name": "Nexus FX Provider", "actor_type": "FXP", "country_code": None, "status": "ACTIVE"},
        {"bic": "WISEFXP", "name": "Wise FX", "actor_type": "FXP", "country_code": None, "status": "ACTIVE"},
    ],
    "fx_rates": [
        {"source_currency": "SGD", "dest_currency": "THB", "rate": 25.45, "spread_bps": 30, "fxp_code": "NEXUSFXP"},
        {"source_currency": "SGD", "dest_currency": "MYR", "rate": 3.45, "spread_bps": 25, "fxp_code": "NEXUSFXP"},
        {"source_currency": "SGD", "dest_currency": "PHP", "rate": 42.15, "spread_bps": 35, "fxp_code": "NEXUSFXP"},
        {"source_currency": "SGD", "dest_currency": "IDR", "rate": 11500.0, "spread_bps": 40, "fxp_code": "NEXUSFXP"},
        {"source_currency": "SGD", "dest_currency": "INR", "rate": 62.30, "spread_bps": 30, "fxp_code": "NEXUSFXP"},
        {"source_currency": "THB", "dest_currency": "SGD", "rate": 0.0393, "spread_bps": 30, "fxp_code": "NEXUSFXP"},
        {"source_currency": "MYR", "dest_currency": "SGD", "rate": 0.290, "spread_bps": 25, "fxp_code": "NEXUSFXP"},
        {"source_currency": "SGD", "dest_currency": "THB", "rate": 25.50, "spread_bps": 25, "fxp_code": "WISEFXP"},
        {"source_currency": "SGD", "dest_currency": "MYR", "rate": 3.48, "spread_bps": 20, "fxp_code": "WISEFXP"},
    ],
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    if engine:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        if async_session:
            async with async_session() as db:
                await seed_data(db)
    yield


async def seed_data(db: AsyncSession):
    result = await db.execute(select(Country).limit(1))
    if result.scalar_one_or_none():
        return
    
    for c in SEED_DATA["countries"]:
        db.add(Country(**c))
    for a in SEED_DATA["actors"]:
        db.add(Actor(**a))
    for r in SEED_DATA["fx_rates"]:
        db.add(FXRate(**r))
    await db.commit()


app = FastAPI(
    title="Nexus Gateway API",
    description="Python Backend for Nexus Sandbox",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/")
async def root():
    return {"name": "Nexus Gateway API", "version": "1.0.0", "status": "sandbox"}


@app.get("/v1/countries")
async def get_countries(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Country))
    countries = result.scalars().all()
    return {
        "countries": [
            {
                "countryId": idx + 1,
                "countryCode": c.code,
                "name": c.name,
                "currencies": [
                    {"currencyCode": c.currency_code, "maxAmount": str(c.max_amount)}
                ],
                "requiredMessageElements": {"pacs008": []},
                "ipsName": c.ips_name,
            }
            for idx, c in enumerate(countries)
        ]
    }


@app.get("/v1/countries/{country_code}/addressTypesAndInputs")
async def get_address_types(country_code: str):
    address_types = {
        "SG": [{"addressTypeId": "MBNO", "addressTypeName": "Mobile Number", "inputs": [{"fieldName": "value", "displayLabel": "Mobile Number", "dataType": "text", "attributes": {"required": True, "pattern": "^\\+65[0-9]{8}$"}}]},
               {"addressTypeId": "NRIC", "addressTypeName": "NRIC/FIN", "inputs": [{"fieldName": "value", "displayLabel": "NRIC/FIN", "dataType": "text", "attributes": {"required": True}}]}],
        "TH": [{"addressTypeId": "MBNO", "addressTypeName": "Mobile Number", "inputs": [{"fieldName": "value", "displayLabel": "Mobile Number", "dataType": "text", "attributes": {"required": True, "pattern": "^\\+66[0-9]{9}$"}}]},
               {"addressTypeId": "NATID", "addressTypeName": "National ID", "inputs": [{"fieldName": "value", "displayLabel": "National ID", "dataType": "text", "attributes": {"required": True}}]}],
        "MY": [{"addressTypeId": "MBNO", "addressTypeName": "Mobile Number", "inputs": [{"fieldName": "value", "displayLabel": "Mobile Number", "dataType": "text", "attributes": {"required": True}}]},
               {"addressTypeId": "NRIC", "addressTypeName": "MyKad Number", "inputs": [{"fieldName": "value", "displayLabel": "MyKad Number", "dataType": "text", "attributes": {"required": True}}]}],
    }
    return {"countryCode": country_code, "addressTypes": address_types.get(country_code, [])}


@app.get("/v1/quotes/{source_country}/{source_currency}/{dest_country}/{dest_currency}/{amount_currency}/{amount}")
async def get_quotes(
    source_country: str,
    source_currency: str,
    dest_country: str,
    dest_currency: str,
    amount_currency: str,
    amount: float,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FXRate).where(
            FXRate.source_currency == source_currency,
            FXRate.dest_currency == dest_currency,
        )
    )
    rates = result.scalars().all()
    
    if not rates:
        base_rate = 25.0 + random.uniform(-2, 2)
        rates = [type('Rate', (), {'rate': base_rate, 'spread_bps': 30, 'fxp_code': 'NEXUSFXP'})()]
    
    quotes = []
    for rate_obj in rates:
        quote_id = str(uuid.uuid4())
        is_source_amount = amount_currency == source_currency
        
        if is_source_amount:
            source_amt = amount
            dest_amt = amount * rate_obj.rate
        else:
            dest_amt = amount
            source_amt = amount / rate_obj.rate
        
        quote = Quote(
            quote_id=quote_id,
            source_country=source_country,
            source_currency=source_currency,
            dest_country=dest_country,
            dest_currency=dest_currency,
            source_amount=source_amt,
            dest_amount=dest_amt,
            exchange_rate=rate_obj.rate,
            fxp_code=rate_obj.fxp_code,
            fxp_name=f"{rate_obj.fxp_code} Provider",
            spread_bps=rate_obj.spread_bps,
            valid_until=datetime.now(timezone.utc) + timedelta(minutes=5),
        )
        db.add(quote)
        quotes.append({
            "quoteId": quote_id,
            "sourceCountry": source_country,
            "sourceCurrency": source_currency,
            "destCountry": dest_country,
            "destCurrency": dest_currency,
            "sourceAmount": round(source_amt, 2),
            "destAmount": round(dest_amt, 2),
            "exchangeRate": rate_obj.rate,
            "fxpCode": rate_obj.fxp_code,
            "fxpName": f"{rate_obj.fxp_code} Provider",
            "spreadBps": rate_obj.spread_bps,
            "validUntil": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
        })
    
    await db.commit()
    return {"quotes": quotes}


@app.get("/v1/fees-and-amounts")
async def get_fees(quoteId: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Quote).where(Quote.quote_id == quoteId))
    quote = result.scalar_one_or_none()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    source_psp_fee = round(quote.source_amount * 0.001, 2)
    dest_psp_fee = round(quote.dest_amount * 0.001, 2)
    fx_margin = round(quote.source_amount * (quote.spread_bps / 10000), 2)
    nexus_fee = round(quote.source_amount * 0.0005, 2)
    
    return {
        "quoteId": quoteId,
        "sourceAmount": quote.source_amount,
        "sourceCurrency": quote.source_currency,
        "destinationAmount": quote.dest_amount,
        "destinationCurrency": quote.dest_currency,
        "exchangeRate": quote.exchange_rate,
        "fees": {
            "sourcePspFee": {"amount": source_psp_fee, "currency": quote.source_currency, "description": "Source PSP Fee"},
            "destinationPspFee": {"amount": dest_psp_fee, "currency": quote.dest_currency, "description": "Destination PSP Fee"},
            "fxMargin": {"amount": fx_margin, "currency": quote.source_currency, "description": "FX Spread"},
            "nexusFee": {"amount": nexus_fee, "currency": quote.source_currency, "description": "Nexus Scheme Fee"},
        },
        "totalSourceDebit": round(quote.source_amount + source_psp_fee + fx_margin + nexus_fee, 2),
        "totalDestinationCredit": round(quote.dest_amount - dest_psp_fee, 2),
    }


class ProxyResolveRequest(BaseModel):
    destinationCountry: str
    proxyType: str
    proxyValue: str
    structuredData: Optional[dict] = None


@app.post("/v1/addressing/resolve")
async def resolve_proxy(req: ProxyResolveRequest, db: AsyncSession = Depends(get_db)):
    bic_map = {"SG": "DBSSSGSG", "TH": "BKKBTHBK", "MY": "MAYBMYKL", "PH": "BNORPHMM", "ID": "BMRIIDJA", "IN": "HABORIN"}
    return {
        "status": "VALIDATED",
        "resolutionId": str(uuid.uuid4()),
        "accountNumber": f"****{random.randint(1000, 9999)}",
        "accountType": "SVGS",
        "agentBic": bic_map.get(req.destinationCountry, "UNKNOWNX"),
        "beneficiaryName": f"Verified Recipient ({req.proxyValue[:4]}***)",
        "displayName": f"V. Recipient",
        "verified": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/v1/quotes/{quote_id}/intermediary-agents")
async def get_intermediary_agents(quote_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Quote).where(Quote.quote_id == quote_id))
    quote = result.scalar_one_or_none()
    
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    return {
        "quoteId": quote_id,
        "sourceSap": {"bic": "DBSSSGSG", "name": "DBS Settlement", "country": quote.source_country},
        "destinationSap": {"bic": "BKKBTHBK", "name": "Bangkok Bank Settlement", "country": quote.dest_country},
        "routingPath": ["S-PSP", "S-IPS", "Nexus", "FXP", "SAP", "D-IPS", "D-PSP"],
    }


@app.post("/v1/iso20022/pacs008")
async def submit_pacs008(pacs002Endpoint: str = Query(default=""), db: AsyncSession = Depends(get_db)):
    uetr = str(uuid.uuid4())
    payment = Payment(
        uetr=uetr,
        status="ACSC",
        source_amount=1000,
        source_currency="SGD",
        dest_amount=25000,
        dest_currency="THB",
        exchange_rate=25.0,
        debtor_name="Demo Sender",
        creditor_name="Demo Recipient",
        completed_at=datetime.now(timezone.utc),
    )
    db.add(payment)
    await db.commit()
    
    return {
        "uetr": uetr,
        "status": "ACSC",
        "message": "Payment completed successfully",
        "callbackEndpoint": pacs002Endpoint,
        "processedAt": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/v1/actors")
async def get_actors(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Actor))
    actors = result.scalars().all()
    return {
        "actors": [
            {"bic": a.bic, "name": a.name, "actorType": a.actor_type, "countryCode": a.country_code, "status": a.status}
            for a in actors
        ],
        "total": len(actors),
    }


class ActorRegisterRequest(BaseModel):
    bic: str
    name: str
    actorType: str
    countryCode: Optional[str] = None
    callbackUrl: Optional[str] = None


@app.post("/v1/actors/register")
async def register_actor(req: ActorRegisterRequest, db: AsyncSession = Depends(get_db)):
    actor = Actor(
        bic=req.bic,
        name=req.name,
        actor_type=req.actorType,
        country_code=req.countryCode,
        callback_url=req.callbackUrl,
        status="ACTIVE",
    )
    db.add(actor)
    await db.commit()
    return {"bic": actor.bic, "name": actor.name, "status": "REGISTERED"}


@app.delete("/v1/actors/{bic}")
async def delete_actor(bic: str, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(Actor).where(Actor.bic == bic))
    await db.commit()
    return {"bic": bic, "status": "DELETED"}


@app.get("/v1/rates")
async def get_rates(corridor: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FXRate))
    rates = result.scalars().all()
    return {
        "rates": [
            {
                "sourceCurrency": r.source_currency,
                "destinationCurrency": r.dest_currency,
                "rate": r.rate,
                "spreadBps": r.spread_bps,
                "fxpCode": r.fxp_code,
            }
            for r in rates
        ]
    }


@app.get("/v1/psps")
async def get_psps(countryCode: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(Actor).where(Actor.actor_type == "PSP")
    if countryCode:
        query = query.where(Actor.country_code == countryCode)
    result = await db.execute(query)
    psps = result.scalars().all()
    return {
        "psps": [
            {"psp_id": p.bic, "bic": p.bic, "name": p.name, "country_code": p.country_code, "fee_percent": 0.1}
            for p in psps
        ],
        "total": len(psps),
    }


@app.get("/v1/ips")
async def get_ips(countryCode: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(Actor).where(Actor.actor_type == "IPS")
    if countryCode:
        query = query.where(Actor.country_code == countryCode)
    result = await db.execute(query)
    ips_list = result.scalars().all()
    
    return {
        "operators": [
            {"ips_id": i.bic, "name": i.name, "country_code": i.country_code, "clearing_system_id": i.bic, "max_amount": 200000, "currency_code": "SGD"}
            for i in ips_list
        ],
        "total": len(ips_list),
    }


@app.get("/v1/pdos")
async def get_pdos(countryCode: Optional[str] = None):
    pdos = [
        {"pdo_id": "PDO_SG", "name": "PayNow Directory", "country_code": "SG", "supported_proxy_types": ["MBNO", "NRIC", "UEN"]},
        {"pdo_id": "PDO_TH", "name": "PromptPay Directory", "country_code": "TH", "supported_proxy_types": ["MBNO", "NATID"]},
        {"pdo_id": "PDO_MY", "name": "DuitNow Directory", "country_code": "MY", "supported_proxy_types": ["MBNO", "NRIC", "PSPT"]},
    ]
    if countryCode:
        pdos = [p for p in pdos if p["country_code"] == countryCode]
    return {"pdos": pdos, "total": len(pdos)}


@app.get("/v1/payments")
async def list_payments(status: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(Payment)
    if status:
        query = query.where(Payment.status == status)
    result = await db.execute(query)
    payments = result.scalars().all()
    return {
        "payments": [
            {
                "uetr": p.uetr,
                "status": p.status,
                "sourceAmount": p.source_amount,
                "sourceCurrency": p.source_currency,
                "destAmount": p.dest_amount,
                "destCurrency": p.dest_currency,
                "debtorName": p.debtor_name,
                "creditorName": p.creditor_name,
                "createdAt": p.created_at.isoformat() if p.created_at else None,
            }
            for p in payments
        ]
    }


@app.get("/v1/payments/{uetr}/status")
async def get_payment_status(uetr: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Payment).where(Payment.uetr == uetr))
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return {
        "uetr": payment.uetr,
        "status": payment.status,
        "statusReasonCode": payment.status_reason_code,
        "sourcePsp": payment.debtor_agent_bic or "DBSSSGSG",
        "destinationPsp": payment.creditor_agent_bic or "BKKBTHBK",
        "amount": payment.source_amount,
        "currency": payment.source_currency,
        "initiatedAt": payment.created_at.isoformat() if payment.created_at else None,
        "completedAt": payment.completed_at.isoformat() if payment.completed_at else None,
    }


@app.get("/v1/payments/{uetr}/events")
async def get_payment_events(uetr: str):
    now = datetime.now(timezone.utc)
    return {
        "uetr": uetr,
        "events": [
            {"step": 1, "name": "Payment Initiated", "status": "completed", "timestamp": (now - timedelta(seconds=10)).isoformat()},
            {"step": 2, "name": "Quote Locked", "status": "completed", "timestamp": (now - timedelta(seconds=8)).isoformat()},
            {"step": 3, "name": "Proxy Resolved", "status": "completed", "timestamp": (now - timedelta(seconds=6)).isoformat()},
            {"step": 4, "name": "pacs.008 Sent", "status": "completed", "timestamp": (now - timedelta(seconds=4)).isoformat()},
            {"step": 5, "name": "FX Conversion", "status": "completed", "timestamp": (now - timedelta(seconds=2)).isoformat()},
            {"step": 6, "name": "Credited to Recipient", "status": "completed", "timestamp": now.isoformat()},
        ],
    }


@app.get("/v1/payments/{uetr}/messages")
async def get_payment_messages(uetr: str):
    return {
        "messages": [
            {"messageType": "pacs.008", "direction": "outbound", "xml": "<pacs.008>...</pacs.008>", "timestamp": datetime.now(timezone.utc).isoformat()},
            {"messageType": "pacs.002", "direction": "inbound", "xml": "<pacs.002>...</pacs.002>", "timestamp": datetime.now(timezone.utc).isoformat()},
        ]
    }


@app.get("/v1/demo-data/stats")
async def get_demo_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Payment))
    payments = result.scalars().all()
    result_q = await db.execute(select(Quote))
    quotes = result_q.scalars().all()
    
    return {
        "totalPayments": len(payments),
        "paymentsByStatus": {},
        "totalQuotes": len(quotes),
        "totalEvents": len(payments) * 6,
        "oldestPayment": None,
        "newestPayment": None,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
