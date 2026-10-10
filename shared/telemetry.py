import os

from fastapi import FastAPI

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)

from opentelemetry.instrumentation.fastapi import (
    FastAPIInstrumentor,
)


def setup_tracer(service_name: str):

    service_name = os.getenv(
        "OTEL_SERVICE_NAME",
        service_name,
    )

    endpoint = os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "http://jaeger:4317",
    )

    resource = Resource.create({
        "service.name": service_name,
    })

    provider = TracerProvider(
        resource=resource
    )

    exporter = OTLPSpanExporter(
        endpoint=endpoint,
        insecure=True,
    )

    provider.add_span_processor(
        BatchSpanProcessor(exporter)
    )

    trace.set_tracer_provider(provider)

    return trace.get_tracer(service_name)


def setup_telemetry(
    app: FastAPI,
    service_name: str,
):

    setup_tracer(service_name)

    FastAPIInstrumentor.instrument_app(app)