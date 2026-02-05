"""
SQLAlchemy models for Nexus Global Payments.

Based on POSTGRESQL_SCHEMA.md with spec-driven design from NotebookLM queries.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import (
    Boolean, Column, ForeignKey, Index, Integer, Numeric, String, Text,
    CheckConstraint, UniqueConstraint, DateTime
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from src.db import Base


# =============================================================================
# Countries & Currencies
# =============================================================================

class Country(Base):
    """Countries enabled for Nexus payments (ISO 3166-1 alpha-2)."""
    __tablename__ = "countries"
    
    country_code: Mapped[str] = mapped_column(String(2), primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    psps: Mapped[List["PSP"]] = relationship("PSP", back_populates="country")
    address_types: Mapped[List["AddressType"]] = relationship("AddressType", back_populates="country")


class Currency(Base):
    """Currencies supported (ISO 4217)."""
    __tablename__ = "currencies"
    
    currency_code: Mapped[str] = mapped_column(String(3), primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    decimal_places: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CountryCurrency(Base):
    """Country-Currency mapping with max amounts."""
    __tablename__ = "country_currencies"
    
    country_code: Mapped[str] = mapped_column(String(2), ForeignKey("countries.country_code"), primary_key=True)
    currency_code: Mapped[str] = mapped_column(String(3), ForeignKey("currencies.currency_code"), primary_key=True)
    max_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_country_currencies_currency", "currency_code"),
    )


# =============================================================================
# Payment Service Providers (PSPs)
# =============================================================================

class PSP(Base):
    """Payment Service Providers (banks, payment institutions)."""
    __tablename__ = "psps"
    
    psp_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    bic: Mapped[str] = mapped_column(String(11), unique=True, nullable=False)  # BIC can be 8 or 11 chars
    name: Mapped[str] = mapped_column(Text, nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), ForeignKey("countries.country_code"), nullable=False)
    is_direct_member: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sponsoring_psp_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("psps.psp_id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    country: Mapped["Country"] = relationship("Country", back_populates="psps")
    sponsoring_psp: Mapped[Optional["PSP"]] = relationship("PSP", remote_side=[psp_id])
    fxp_relationships: Mapped[List["FXPPSPRelationship"]] = relationship("FXPPSPRelationship", back_populates="psp")
    
    __table_args__ = (
        Index("idx_psps_country", "country_code"),
        Index("idx_psps_sponsoring", "sponsoring_psp_id", postgresql_where=Column("sponsoring_psp_id") != None),
    )


# =============================================================================
# FX Providers (FXPs)
# =============================================================================

class FXP(Base):
    """FX Providers."""
    __tablename__ = "fxps"
    
    fxp_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    fxp_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    bic: Mapped[Optional[str]] = mapped_column(String(11), nullable=True)
    legal_entity_identifier: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    psp_relationships: Mapped[List["FXPPSPRelationship"]] = relationship("FXPPSPRelationship", back_populates="fxp")
    rate_tiers: Mapped[List["RateTier"]] = relationship("RateTier", back_populates="fxp")
    accounts: Mapped[List["FXPAccount"]] = relationship("FXPAccount", back_populates="fxp")


class FXPPSPRelationship(Base):
    """FXP-PSP relationships for PSP-specific rate improvements.
    
    Reference: NotebookLM 2026-02-03 - FXPs perform KYB via Wolfsberg CBDDQ
    """
    __tablename__ = "fxp_psp_relationships"
    
    fxp_id: Mapped[int] = mapped_column(Integer, ForeignKey("fxps.fxp_id"), primary_key=True)
    psp_id: Mapped[int] = mapped_column(Integer, ForeignKey("psps.psp_id"), primary_key=True)
    relationship_type: Mapped[str] = mapped_column(
        String(20), 
        nullable=False,
        default="ONBOARDED"
    )
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rate_improvement_bps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    kyb_reference: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Wolfsberg CBDDQ ref
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    fxp: Mapped["FXP"] = relationship("FXP", back_populates="psp_relationships")
    psp: Mapped["PSP"] = relationship("PSP", back_populates="fxp_relationships")
    
    __table_args__ = (
        Index("idx_fxp_psp_psp", "psp_id"),
        CheckConstraint("relationship_type IN ('ONBOARDED', 'PREFERRED', 'PENDING_KYB')", name="ck_relationship_type"),
    )


# =============================================================================
# Settlement Access Providers (SAPs)
# =============================================================================

class SAP(Base):
    """Settlement Access Providers (PSPs that provide accounts to FXPs)."""
    __tablename__ = "saps"
    
    sap_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    psp_id: Mapped[int] = mapped_column(Integer, ForeignKey("psps.psp_id"), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), ForeignKey("countries.country_code"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint("psp_id", "country_code", name="uq_sap_psp_country"),
    )


class FXPAccount(Base):
    """FXP accounts held at SAPs for settlement."""
    __tablename__ = "fxp_accounts"
    
    fxp_account_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fxp_id: Mapped[int] = mapped_column(Integer, ForeignKey("fxps.fxp_id"), nullable=False)
    sap_id: Mapped[int] = mapped_column(Integer, ForeignKey("saps.sap_id"), nullable=False)
    account_number: Mapped[str] = mapped_column(Text, nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), ForeignKey("currencies.currency_code"), nullable=False)
    account_type: Mapped[str] = mapped_column(String(20), default="OPERATING", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    fxp: Mapped["FXP"] = relationship("FXP", back_populates="accounts")
    
    __table_args__ = (
        UniqueConstraint("fxp_id", "sap_id", "currency_code", "account_type", name="uq_fxp_account"),
        Index("idx_fxp_accounts_fxp", "fxp_id"),
        Index("idx_fxp_accounts_sap", "sap_id"),
        CheckConstraint("account_type IN ('OPERATING', 'LIQUIDITY')", name="ck_account_type"),
    )


# =============================================================================
# FX Rates & Tiers
# =============================================================================

class RateTier(Base):
    """Tier-based rate improvements.
    
    Reference: NotebookLM 2026-02-03 - FXPs POST /tiers for volume thresholds
    """
    __tablename__ = "rate_tiers"
    
    tier_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fxp_id: Mapped[int] = mapped_column(Integer, ForeignKey("fxps.fxp_id"), nullable=False)
    source_currency: Mapped[str] = mapped_column(String(3), ForeignKey("currencies.currency_code"), nullable=False)
    destination_currency: Mapped[str] = mapped_column(String(3), ForeignKey("currencies.currency_code"), nullable=False)
    min_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    max_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    improvement_bps: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    fxp: Mapped["FXP"] = relationship("FXP", back_populates="rate_tiers")
    
    __table_args__ = (
        Index("idx_rate_tiers_fxp_pair", "fxp_id", "source_currency", "destination_currency"),
        CheckConstraint("max_amount IS NULL OR max_amount > min_amount", name="ck_tier_amount_range"),
    )


# =============================================================================
# Quotes
# =============================================================================

class Quote(Base):
    """Payment-specific FX quotes (10-minute TTL).
    
    Reference: NotebookLM 2026-02-03 - Quotes valid for 600 seconds
    """
    __tablename__ = "quotes"
    
    quote_id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    fxp_id: Mapped[int] = mapped_column(Integer, ForeignKey("fxps.fxp_id"), nullable=False)
    source_country: Mapped[str] = mapped_column(String(2), nullable=False)
    destination_country: Mapped[str] = mapped_column(String(2), nullable=False)
    source_currency: Mapped[str] = mapped_column(String(3), ForeignKey("currencies.currency_code"), nullable=False)
    destination_currency: Mapped[str] = mapped_column(String(3), ForeignKey("currencies.currency_code"), nullable=False)
    base_rate: Mapped[Decimal] = mapped_column(Numeric(18, 10), nullable=False)
    spread_bps: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    tier_improvement_bps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    psp_improvement_bps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    final_rate: Mapped[Decimal] = mapped_column(Numeric(18, 10), nullable=False)
    requested_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    source_interbank_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    destination_interbank_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    creditor_account_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    destination_psp_fee: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    amount_type: Mapped[str] = mapped_column(String(20), default="SOURCE", nullable=False)
    capped_to_max_amount: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    
    __table_args__ = (
        Index("idx_quotes_psp", "psp_id"),
        Index("idx_quotes_fxp", "fxp_id"),
        Index("idx_quotes_expires", "expires_at"),
        CheckConstraint("amount_type IN ('SOURCE', 'DESTINATION')", name="ck_amount_type"),
    )


# =============================================================================
# Payments
# =============================================================================

class Payment(Base):
    """Payment transactions (core table).
    
    Note: In production, this should be partitioned by created_at
    """
    __tablename__ = "payments"
    
    payment_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uetr: Mapped[str] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False)
    quote_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True), ForeignKey("quotes.quote_id"), nullable=True)
    
    # Sender details
    source_psp_id: Mapped[int] = mapped_column(Integer, ForeignKey("psps.psp_id"), nullable=False)
    source_country_code: Mapped[str] = mapped_column(String(2), ForeignKey("countries.country_code"), nullable=False)
    debtor_name: Mapped[str] = mapped_column(Text, nullable=False)
    debtor_account: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Recipient details
    destination_psp_id: Mapped[int] = mapped_column(Integer, ForeignKey("psps.psp_id"), nullable=False)
    destination_country_code: Mapped[str] = mapped_column(String(2), ForeignKey("countries.country_code"), nullable=False)
    creditor_name: Mapped[str] = mapped_column(Text, nullable=False)
    creditor_account: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Amounts
    debtor_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    debtor_currency: Mapped[str] = mapped_column(String(3), ForeignKey("currencies.currency_code"), nullable=False)
    source_interbank_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    destination_interbank_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    creditor_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    creditor_currency: Mapped[str] = mapped_column(String(3), ForeignKey("currencies.currency_code"), nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(18, 10), nullable=False)
    
    # Fees
    source_psp_fee: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    destination_psp_fee: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    
    # FX Provider
    fxp_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("fxps.fxp_id"), nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    priority: Mapped[str] = mapped_column(String(10), default="NORM", nullable=False)
    
    # Purpose
    purpose_code: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    remittance_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Raw message storage (for audit)
    pacs008_message: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    pacs002_message: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    __table_args__ = (
        Index("idx_payments_source_psp", "source_psp_id", "created_at"),
        Index("idx_payments_dest_psp", "destination_psp_id", "created_at"),
        Index("idx_payments_status", "status", postgresql_where=Column("status").notin_(["COMPLETED", "REJECTED"])),
        Index("idx_payments_created", "created_at"),
        CheckConstraint(
            "status IN ('PENDING', 'SUBMITTED', 'ACCEPTED', 'REJECTED', 'BLOCKED', 'COMPLETED', 'RETURNED')",
            name="ck_payment_status"
        ),
        CheckConstraint("priority IN ('NORM', 'HIGH')", name="ck_payment_priority"),
    )


# =============================================================================
# Payment Events (Event Sourcing)
# =============================================================================

class PaymentEvent(Base):
    """Immutable event log for payment state changes."""
    __tablename__ = "payment_events"
    
    event_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_id: Mapped[int] = mapped_column(Integer, nullable=False)  # No FK for performance
    uetr: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    actor: Mapped[str] = mapped_column(Text, nullable=False)
    correlation_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_payment_events_uetr", "uetr"),
        Index("idx_payment_events_payment", "payment_id"),
        Index("idx_payment_events_type", "event_type", "created_at"),
        CheckConstraint(
            """event_type IN (
                'PAYMENT_INITIATED', 'QUOTE_SELECTED', 'PAYMENT_SUBMITTED',
                'PAYMENT_FORWARDED', 'PAYMENT_ACCEPTED', 'PAYMENT_REJECTED',
                'PAYMENT_BLOCKED', 'PAYMENT_COMPLETED', 'PAYMENT_RETURNED',
                'INVESTIGATION_REQUESTED', 'INVESTIGATION_RESOLVED'
            )""",
            name="ck_event_type"
        ),
    )


# =============================================================================
# Address Types (for Proxy Resolution)
# =============================================================================

class AddressType(Base):
    """Address types supported by each country."""
    __tablename__ = "address_types"
    
    address_type_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    country_code: Mapped[str] = mapped_column(String(2), ForeignKey("countries.country_code"), nullable=False)
    type_code: Mapped[str] = mapped_column(String(10), nullable=False)  # MOBI, IBAN, ACCT, EMAIL
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    requires_proxy_resolution: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    proxy_directory_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    clearing_system_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    iso20022_path: Mapped[str] = mapped_column(Text, nullable=False)  # XPath in pacs.008
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    country: Mapped["Country"] = relationship("Country", back_populates="address_types")
    inputs: Mapped[List["AddressInput"]] = relationship("AddressInput", back_populates="address_type")
    
    __table_args__ = (
        UniqueConstraint("country_code", "type_code", name="uq_address_type_country"),
        Index("idx_address_types_country", "country_code"),
    )


class AddressInput(Base):
    """Address input fields for UI generation."""
    __tablename__ = "address_inputs"
    
    input_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    address_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("address_types.address_type_id"), nullable=False)
    field_name: Mapped[str] = mapped_column(Text, nullable=False)
    display_label: Mapped[str] = mapped_column(Text, nullable=False)
    input_type: Mapped[str] = mapped_column(String(20), default="TEXT", nullable=False)
    validation_pattern: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    max_length: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    address_type: Mapped["AddressType"] = relationship("AddressType", back_populates="inputs")
    
    __table_args__ = (
        UniqueConstraint("address_type_id", "field_name", name="uq_address_input_field"),
        Index("idx_address_inputs_type", "address_type_id"),
        CheckConstraint("input_type IN ('TEXT', 'SELECT', 'TEL', 'EMAIL')", name="ck_input_type"),
    )


# =============================================================================
# Compliance & Audit
# =============================================================================

class ScreeningResult(Base):
    """Sanctions screening results for compliance audit."""
    __tablename__ = "screening_results"
    
    screening_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_id: Mapped[int] = mapped_column(Integer, nullable=False)
    uetr: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    screening_type: Mapped[str] = mapped_column(String(20), nullable=False)
    screened_by: Mapped[str] = mapped_column(Text, nullable=False)  # PSP BIC or 'NEXUS'
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    list_matched: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    match_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    decision: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    decided_by: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_screening_payment", "payment_id"),
        Index("idx_screening_uetr", "uetr"),
        Index("idx_screening_result", "result", postgresql_where=Column("result") != "CLEAR"),
        CheckConstraint("screening_type IN ('SENDER', 'RECIPIENT', 'PAYMENT')", name="ck_screening_type"),
        CheckConstraint("result IN ('CLEAR', 'MATCH', 'POTENTIAL_MATCH', 'ERROR')", name="ck_screening_result"),
        CheckConstraint("decision IS NULL OR decision IN ('APPROVED', 'BLOCKED', 'PENDING_REVIEW')", name="ck_screening_decision"),
    )
