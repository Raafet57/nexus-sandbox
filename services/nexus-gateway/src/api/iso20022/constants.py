"""
ISO 20022 Constants per Nexus Specification

This module contains all constant values used in ISO 20022 message processing,
including status reason codes, timing configurations, and validation patterns.

Reference: https://docs.nexusglobalpayments.org/messaging-and-translation/key-points
"""

import re

# =============================================================================
# Timing Constants
# =============================================================================

QUOTE_EXPIRY_SECONDS = 600  # 10 minutes - FXPs must honour quotes for this duration

# =============================================================================
# UETR Patterns for Return Payments
# =============================================================================

# NexusOrgnlUETR prefix for pacs.008 return payments
# Reference: NotebookLM 2026-02-03 - "Include original UETR prefixed with NexusOrgnlUETR:"
# Made flexible to accept: NexusOrgnlUETR:uuid, NexusOrgnlUETR: uuid, NexusOrgnlUETR uuid, etc.
NEXUS_ORIGINAL_UETR_PREFIX = "NexusOrgnlUETR:"
NEXUS_ORIGINAL_UETR_PATTERN = re.compile(r"NexusOrgnlUETR[:\\s]+([a-f0-9\\-]{36})", re.IGNORECASE)

# =============================================================================
# ISO 20022 Status Reason Codes (ExternalStatusReason1Code)
# Reference: NotebookLM - Technical Assumptions A20
# Assumption A28: Sandbox implements subset of 60+ production codes
# =============================================================================

# Success
STATUS_ACCEPTED = "ACCC"            # Accepted Settlement Completed

# Quote/Rate Errors (AB04: Aborted - Settlement Fatal Error)
STATUS_QUOTE_EXPIRED = "AB04"       # Quote validity window exceeded
STATUS_RATE_MISMATCH = "AB04"       # Agreed rate doesn't match stored quote

# Timeout Errors
STATUS_TIMEOUT = "AB03"             # Transaction not received within window

# Account Errors
STATUS_ACCOUNT_INCORRECT = "AC01"   # Incorrect Account Number format
STATUS_ACCOUNT_CLOSED = "AC04"      # Closed Account Number
STATUS_PROXY_INVALID = "BE23"       # Account/Proxy Invalid (not registered)

# Agent Errors
STATUS_AGENT_INCORRECT = "AGNT"     # Incorrect Agent (PSP not onboarded)
STATUS_INVALID_SAP = "RC11"         # Invalid Intermediary Agent
STATUS_AGENT_OFFLINE = "AB08"       # Offline Creditor Agent

# Amount Errors
STATUS_AMOUNT_LIMIT = "AM02"        # IPS Limit exceeded
STATUS_INSUFFICIENT_FUNDS = "AM04"  # Insufficient Funds

# Compliance Errors
STATUS_REGULATORY_AML = "RR04"      # Regulatory/AML block

# Additional ISO 20022 ExternalStatusReason1Code values per Nexus spec
AB01 = "AB01"  # Aborted Clearing Timeout
AB02 = "AB02"  # Aborted Clearing Fatal Error
AB05 = "AB05"  # Timeout Creditor Agent
AB06 = "AB06"  # Timeout Instructed Agent
AB09 = "AB09"  # Error Creditor Agent
AB10 = "AB10"  # Error Instructed Agent
AC06 = "AC06"  # Blocked Account
AC07 = "AC07"  # Closed Creditor Account Number
AC14 = "AC14"  # Invalid Creditor Account Type
AG01 = "AG01"  # Transaction Forbidden
AG03 = "AG03"  # Transaction Not Supported
AG11 = "AG11"  # Creditor Agent Suspended
AM03 = "AM03"  # Not Allowed Currency
AM05 = "AM05"  # Duplication
AM06 = "AM06"  # Too Low Amount
AM07 = "AM07"  # Blocked Amount
AM13 = "AM13"  # Amount Exceeds Clearing System Limit
AM14 = "AM14"  # Amount Exceeds Agreed Limit
BE01 = "BE01"  # Inconsistent With End Customer
BE04 = "BE04"  # Missing Creditor Address
BE05 = "BE05"  # Unrecognised Initiating Party
BE06 = "BE06"  # Unknown End Customer
BE07 = "BE07"  # Missing Debtor Address
CH11 = "CH11"  # Creditor Identifier Incorrect
CH20 = "CH20"  # Decimal Points Not Compatible With Currency
CH21 = "CH21"  # Required Compulsory Element Missing
CNOR = "CNOR"  # Creditor Bank Is Not Registered
CURR = "CURR"  # Incorrect Currency
DU01 = "DU01"  # Duplicate - Same EndToEndId
DU02 = "DU02"  # Duplicate - Same UETR
ED05 = "ED05"  # Settlement Failed
ED06 = "ED06"  # Settlement System Not Available
FF10 = "FF10"  # Bank System Processing Error
FR01 = "FR01"  # Fraud
MD07 = "MD07"  # End Customer Deceased
MS02 = "MS02"  # Not Specified Reason Customer Generated
MS03 = "MS03"  # Not Specified Reason Agent Generated
NARR = "NARR"  # Narrative
RC04 = "RC04"  # Invalid Creditor Bank Identifier
RC07 = "RC07"  # Invalid Creditor BIC Identifier
RC10 = "RC10"  # Invalid Creditor Clearing System Member Identifier
RR02 = "RR02"  # Missing Debtor Name Or Address
RR03 = "RR03"  # Missing Creditor Name Or Address
TM01 = "TM01"  # Invalid Cut-Off Time
UCRD = "UCRD"  # Unknown Creditor

# All status codes for validation (comprehensive list per Nexus spec)
VALID_STATUS_CODES = {
    STATUS_ACCEPTED, STATUS_QUOTE_EXPIRED, STATUS_RATE_MISMATCH,
    STATUS_TIMEOUT, STATUS_ACCOUNT_INCORRECT, STATUS_ACCOUNT_CLOSED,
    STATUS_PROXY_INVALID, STATUS_AGENT_INCORRECT, STATUS_INVALID_SAP,
    STATUS_AGENT_OFFLINE, STATUS_AMOUNT_LIMIT, STATUS_INSUFFICIENT_FUNDS,
    STATUS_REGULATORY_AML,
    # Additional codes
    AB01, AB02, AB05, AB06, AB09, AB10,
    AC06, AC07, AC14,
    AG01, AG03, AG11,
    AM03, AM05, AM06, AM07, AM13, AM14,
    BE01, BE04, BE05, BE06, BE07,
    CH11, CH20, CH21,
    CNOR, CURR,
    DU01, DU02,
    ED05, ED06,
    FF10, FR01,
    MD07, MS02, MS03, NARR,
    RC04, RC07, RC10,
    RR02, RR03,
    TM01, UCRD
}
