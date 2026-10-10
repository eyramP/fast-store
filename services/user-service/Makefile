run-user-service:
    uv run --package user-service fastapi dev services/user-service/main.py --port 8001

add_sqlmpdel:
    uv add sqlmodel --package user-service

run_python_grpc
     uv run python -m grpc_tools.protoc -I protos --python_out=services/product-service --grpc_python_out=services/product-service protos/product.proto

install-tracing:
    uv add opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi opentelemetry-exporter-otlp --package user-service

create-user-service-image-for-k8s:
    docker build -t user-service:latest -f services/user-service/Dockerfile .

build-product-service-image-for-k8s:
    minikube image build -t product-service:latest -f services/product-service/Dockerfile .
deploy product-service:
    kubectl apply -f k8s/product-service.yaml
list-image-in-minikube:
    minikube image ls | grep order-service

check-kube-memory-usage:
     kubectl top nodes

Grafana_P: FastStoreGrafana2026!

Run prometheus:
    kubectl port-forward service/prometheus 9090:9090
run grafana:
    kubectl port-forward svc/grafana 3000:3000
get running pods:
    kubectl get pods
detailed about a particular_pod:
    kubectl describe pod <pod-name>