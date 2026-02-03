"""
Application configuration.

Settings are loaded from environment variables with sensible defaults
for sandbox development.
"""

from pydantic_settings import BaseSettings


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
    
    # Security
    jwt_secret: str = "nexus-sandbox-jwt-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    
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
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
