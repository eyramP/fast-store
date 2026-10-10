from opentelemetry import propagate


def inject_grpc_metadata():
    metadata = {}

    propagate.inject(metadata)

    return tuple(metadata.items())