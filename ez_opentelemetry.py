from opentelemetry.trace import StatusCode, Status  # Trace statuses
from opentelemetry import context                   # Context functionality
from opentelemetry import propagate                 # Trace context propagation
from opentelemetry import trace, baggage            # Trace and baggage functionality
from opentelemetry.sdk.resources import Resource    # Define resources in tracing
from opentelemetry.sdk.trace import TracerProvider  # Trace functionality
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter  # Span exporters for OTLP server using gRPC
from opentelemetry.sdk.trace.export import (        # Generic span exporters
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor
)
from opentelemetry.semconv.trace import (               # Standard semantic conventions for tracing
    SpanAttributes,
    MessagingDestinationKindValues,
    MessagingOperationValues
)
from solace_otel.messaging.trace.propagation import (   # Solace message carriers for trace propagation
    OutboundMessageCarrier,
    OutboundMessageGetter, 
    OutboundMessageSetter,
    InboundMessageCarrier,
    InboundMessageGetter
)

def main():
    return True

if __name__ == "__main__":
    default_setter = OutboundMessageSetter()
    propagator = propagate.get_global_textmap()
    tracer = trace.get_tracer("ez_tracer")
    main()