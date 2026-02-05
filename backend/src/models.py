from sqlalchemy import Column, String, Float, DateTime, Integer, JSON, Text
from sqlalchemy.sql import func
from src.database import Base

class Country(Base):
    __tablename__ = "countries"
    
    code = Column(String(2), primary_key=True)
    name = Column(String(100), nullable=False)
    currency_code = Column(String(3), nullable=False)
    max_amount = Column(Float, default=50000)
    ips_name = Column(String(100))

class Quote(Base):
    __tablename__ = "quotes"
    
    quote_id = Column(String(36), primary_key=True)
    source_country = Column(String(2), nullable=False)
    source_currency = Column(String(3), nullable=False)
    dest_country = Column(String(2), nullable=False)
    dest_currency = Column(String(3), nullable=False)
    source_amount = Column(Float, nullable=False)
    dest_amount = Column(Float, nullable=False)
    exchange_rate = Column(Float, nullable=False)
    fxp_code = Column(String(20), nullable=False)
    fxp_name = Column(String(100))
    spread_bps = Column(Integer, default=0)
    valid_until = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Payment(Base):
    __tablename__ = "payments"
    
    uetr = Column(String(36), primary_key=True)
    quote_id = Column(String(36))
    status = Column(String(20), default="PENDING")
    status_reason_code = Column(String(10))
    source_amount = Column(Float)
    source_currency = Column(String(3))
    dest_amount = Column(Float)
    dest_currency = Column(String(3))
    exchange_rate = Column(Float)
    debtor_name = Column(String(100))
    debtor_account = Column(String(50))
    debtor_agent_bic = Column(String(11))
    creditor_name = Column(String(100))
    creditor_account = Column(String(50))
    creditor_agent_bic = Column(String(11))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

class Actor(Base):
    __tablename__ = "actors"
    
    bic = Column(String(11), primary_key=True)
    name = Column(String(100), nullable=False)
    actor_type = Column(String(10), nullable=False)  # PSP, IPS, FXP, SAP, PDO
    country_code = Column(String(2))
    status = Column(String(20), default="ACTIVE")
    callback_url = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class FXRate(Base):
    __tablename__ = "fx_rates"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_currency = Column(String(3), nullable=False)
    dest_currency = Column(String(3), nullable=False)
    rate = Column(Float, nullable=False)
    spread_bps = Column(Integer, default=0)
    fxp_code = Column(String(20), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
