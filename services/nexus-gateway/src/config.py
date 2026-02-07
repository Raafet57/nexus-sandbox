"""
Application configuration.

Settings are loaded from environment variables with sensible defaults
for sandbox development.

SECURITY NOTE:
- In production, set NEXUS_JWT_SECRET environment variable
- Never commit production secrets to version control
"""

import os
import secrets
import warnings
from pydantic_settings import BaseSettings


# Development-only default secret (triggers warning)
_DEV_JWT_SECRET = "nexus-sandbox-jwt-secret-dev-only"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql://nexus:nexus_sandbox_password@localhost:5432/nexus"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"

    # OpenTelemetry
    otel_enabled: bool = True
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "nexus-gateway"

    # Security - Load from environment variable NEXUS_JWT_SECRET
    # SECURITY: In production, always set this via environment variable
    jwt_secret: str = os.environ.get("NEXUS_JWT_SECRET", _DEV_JWT_SECRET)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    require_secure_secrets: bool = os.environ.get("REQUIRE_SECURE_SECRETS", "false").lower() == "true"
    
    # Quote settings
    # Reference: https://docs.nexusglobalpayments.org/fx-provision/quotes
    quote_validity_seconds: int = 600  # Scheme mandate: 10 minutes

    
    # Payment SLA
    # Reference: https://docs.nexusglobalpayments.org/payment-setup/step-17-accept-the-confirmation-and-notify-sender
    payment_timeout_seconds: int = 60
    
    # Rate refresh
    rate_refresh_interval_seconds: int = 60
    
    # Retry settings
    max_retries: int = 3

    # Sandbox Demo Defaults
    # These are used when XML parsing returns None for required fields
    demo_debtor_name: str = "Demo Sender"
    demo_debtor_account: str = "SG1234567890"
    demo_creditor_name: str = "Demo Recipient"
    demo_creditor_account: str = "TH9876543210"

    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Security warnings
        if self.jwt_secret == _DEV_JWT_SECRET:
            if self.require_secure_secrets:
                raise ValueError(
                    "SECURITY: Using development JWT secret in production mode. "
                    "Set NEXUS_JWT_SECRET environment variable with a strong secret."
                )
            warnings.warn(
                "SECURITY: Using development JWT secret. Set NEXUS_JWT_SECRET "
                "environment variable for production deployments.",
                stacklevel=2
            )


settings = Settings()
