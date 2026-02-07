-- Migration: FXP and SAP API Tables
-- Description: Add tables for FXP rate management and SAP liquidity operations
-- Date: 2026-02-07
-- Migration: 004 (Renamed from 003_fxp_sap_tables.sql to fix ordering conflict)

-- =============================================================================
-- FXP Rate Management
-- =============================================================================

-- FXP Rates table (for rate submission/withdrawal tracking)
CREATE TABLE IF NOT EXISTS fxp_rates (
    rate_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fxp_id UUID NOT NULL REFERENCES fxps(fxp_id),
    source_currency CHAR(3) NOT NULL REFERENCES currencies(currency_code),
    destination_currency CHAR(3) NOT NULL REFERENCES currencies(currency_code),
    base_rate DECIMAL(18, 8) NOT NULL,
    spread_bps INT NOT NULL DEFAULT 50,
    effective_rate DECIMAL(18, 8) NOT NULL,
    valid_until TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',  -- ACTIVE, WITHDRAWN, EXPIRED
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    withdrawn_at TIMESTAMPTZ
);

CREATE INDEX idx_fxp_rates_fxp ON fxp_rates(fxp_id);
CREATE INDEX idx_fxp_rates_corridor ON fxp_rates(source_currency, destination_currency);
CREATE INDEX idx_fxp_rates_status ON fxp_rates(status) WHERE status = 'ACTIVE';
CREATE INDEX idx_fxp_rates_valid ON fxp_rates(valid_until) WHERE status = 'ACTIVE';

-- FXP-PSP Relationships table (for tier-based rate improvements)
CREATE TABLE IF NOT EXISTS fxp_psp_relationships (
    relationship_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fxp_id UUID NOT NULL REFERENCES fxps(fxp_id),
    psp_id UUID NOT NULL REFERENCES psps(psp_id),
    tier VARCHAR(20) NOT NULL DEFAULT 'STANDARD',  -- STANDARD, VOLUME, PREMIUM
    improvement_bps INT NOT NULL DEFAULT 0,  -- Rate improvement in basis points
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(fxp_id, psp_id)
);

CREATE INDEX idx_fxp_psp_fxp ON fxp_psp_relationships(fxp_id);
CREATE INDEX idx_fxp_psp_psp ON fxp_psp_relationships(psp_id);

-- =============================================================================
-- SAP Liquidity Management
-- =============================================================================

-- SAP Reservations table (for liquidity reservations)
CREATE TABLE IF NOT EXISTS sap_reservations (
    reservation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES fxp_sap_accounts(account_id),
    amount DECIMAL(18, 2) NOT NULL,
    uetr UUID NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',  -- ACTIVE, UTILIZED, EXPIRED, CANCELLED
    reserved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    utilized_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ
);

CREATE INDEX idx_sap_reservations_account ON sap_reservations(account_id);
CREATE INDEX idx_sap_reservations_status ON sap_reservations(status) WHERE status = 'ACTIVE';
CREATE INDEX idx_sap_reservations_expires ON sap_reservations(expires_at) WHERE status = 'ACTIVE';
CREATE INDEX idx_sap_reservations_uetr ON sap_reservations(uetr);

-- SAP Transactions table (for settlement transaction logging)
CREATE TABLE IF NOT EXISTS sap_transactions (
    transaction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID NOT NULL REFERENCES fxp_sap_accounts(account_id),
    amount DECIMAL(18, 2) NOT NULL,
    type VARCHAR(10) NOT NULL,  -- DEBIT, CREDIT
    reference VARCHAR(140) NOT NULL,
    uetr UUID,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',  -- PENDING, COMPLETED, FAILED
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_sap_transactions_account ON sap_transactions(account_id);
CREATE INDEX idx_sap_transactions_uetr ON sap_transactions(uetr);
CREATE INDEX idx_sap_transactions_created ON sap_transactions(created_at);

-- =============================================================================
-- Trade Notifications Log
-- =============================================================================

-- Trade notifications sent to FXPs when their rates are selected
CREATE TABLE IF NOT EXISTS trade_notifications (
    notification_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fxp_id UUID NOT NULL REFERENCES fxps(fxp_id),
    quote_id UUID NOT NULL REFERENCES quotes(quote_id),
    uetr UUID NOT NULL,
    source_currency CHAR(3) NOT NULL,
    destination_currency CHAR(3) NOT NULL,
    amount DECIMAL(18, 2) NOT NULL,
    rate DECIMAL(18, 8) NOT NULL,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    delivery_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',  -- PENDING, DELIVERED, FAILED
    retry_count INT NOT NULL DEFAULT 0
);

CREATE INDEX idx_trade_notifications_fxp ON trade_notifications(fxp_id);
CREATE INDEX idx_trade_notifications_quote ON trade_notifications(quote_id);
CREATE INDEX idx_trade_notifications_status ON trade_notifications(delivery_status) WHERE delivery_status != 'DELIVERED';

-- =============================================================================
-- Comments
-- =============================================================================

COMMENT ON TABLE fxp_rates IS 'FXP rate submissions for corridors';
COMMENT ON TABLE fxp_psp_relationships IS 'Relationships between FXPs and PSPs for tier-based improvements';
COMMENT ON TABLE sap_reservations IS 'Liquidity reservations for payments';
COMMENT ON TABLE sap_transactions IS 'Settlement transactions on FXP accounts';
COMMENT ON TABLE trade_notifications IS 'Notifications sent to FXPs when their rates are selected';
