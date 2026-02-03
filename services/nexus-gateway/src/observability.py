"""
OpenTelemetry observability setup.

Reference: ADR on distributed tracing and
https://docs.nexusglobalpayments.org/ best practices for payment observability.
"""

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource

from src.config import settings


def setup_tracing(app):
    """Configure OpenTelemetry tracing."""
    
    # Create resource with service name
    resource = Resource.create({
        "service.name": settings.otel_service_name,
        "service.version": "0.1.0",
    })
    
    # Create tracer provider
    provider = TracerProvider(resource=resource)
    
    # Configure exporter
    exporter = OTLPSpanExporter(
        endpoint=settings.otel_exporter_otlp_endpoint,
        insecure=True,
    )
    
    # Add processor
    provider.add_span_processor(BatchSpanProcessor(exporter))
    
    # Set as global tracer provider
    trace.set_tracer_provider(provider)
    
    return provider


def get_tracer(name: str = "nexus-gateway"):
    """Get a tracer for manual instrumentation."""
    return trace.get_tracer(name)
