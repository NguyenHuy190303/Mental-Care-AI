#!/bin/bash

# Mental Health Agent - Kubernetes Deployment Script
# Production-grade deployment with load balancing and auto-scaling

set -e

# Configuration
NAMESPACE="mental-health-agent"
KUBECTL_CONTEXT=${KUBECTL_CONTEXT:-"production"}
ENVIRONMENT=${ENVIRONMENT:-"production"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    # Check helm
    if ! command -v helm &> /dev/null; then
        log_warning "helm is not installed - some features may not be available"
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check context
    CURRENT_CONTEXT=$(kubectl config current-context)
    log_info "Current kubectl context: $CURRENT_CONTEXT"
    
    if [[ "$CURRENT_CONTEXT" != *"$KUBECTL_CONTEXT"* ]]; then
        log_warning "Current context doesn't match expected context: $KUBECTL_CONTEXT"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    log_success "Prerequisites check completed"
}

# Create namespace and basic resources
create_namespace() {
    log_info "Creating namespace and basic resources..."
    
    kubectl apply -f ../kubernetes/namespace.yaml
    
    # Wait for namespace to be ready
    kubectl wait --for=condition=Ready namespace/$NAMESPACE --timeout=60s
    
    log_success "Namespace created successfully"
}

# Deploy secrets (requires manual setup)
deploy_secrets() {
    log_info "Checking secrets..."
    
    # Check if secrets exist
    if kubectl get secret mental-health-agent-secrets -n $NAMESPACE &> /dev/null; then
        log_success "Secrets already exist"
    else
        log_warning "Secrets not found. Please create secrets manually:"
        echo "1. Copy infrastructure/kubernetes/secrets.yaml"
        echo "2. Replace all REPLACE_WITH_BASE64_ENCODED_* values"
        echo "3. Apply: kubectl apply -f secrets.yaml"
        echo ""
        read -p "Have you created the secrets? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_error "Secrets are required for deployment"
            exit 1
        fi
    fi
}

# Deploy configuration
deploy_config() {
    log_info "Deploying configuration..."
    
    kubectl apply -f ../kubernetes/configmap.yaml
    
    log_success "Configuration deployed successfully"
}

# Deploy databases
deploy_databases() {
    log_info "Deploying database cluster..."
    
    kubectl apply -f ../kubernetes/database-cluster.yaml
    
    # Wait for databases to be ready
    log_info "Waiting for PostgreSQL to be ready..."
    kubectl wait --for=condition=Ready pod -l app=postgres,role=primary -n $NAMESPACE --timeout=300s
    
    log_info "Waiting for Redis to be ready..."
    kubectl wait --for=condition=Ready pod -l app=redis -n $NAMESPACE --timeout=300s
    
    log_info "Waiting for ChromaDB to be ready..."
    kubectl wait --for=condition=Ready pod -l app=chromadb -n $NAMESPACE --timeout=300s
    
    log_success "Database cluster deployed successfully"
}

# Deploy backend services
deploy_backend() {
    log_info "Deploying backend services..."
    
    kubectl apply -f ../kubernetes/backend-deployment.yaml
    
    # Wait for backend to be ready
    log_info "Waiting for backend services to be ready..."
    kubectl wait --for=condition=Available deployment/mental-health-backend -n $NAMESPACE --timeout=300s
    
    # Check HPA
    kubectl get hpa mental-health-backend-hpa -n $NAMESPACE
    
    log_success "Backend services deployed successfully"
}

# Deploy load balancer
deploy_load_balancer() {
    log_info "Deploying load balancer..."
    
    kubectl apply -f ../kubernetes/load-balancer.yaml
    
    # Wait for load balancer to be ready
    log_info "Waiting for load balancer to be ready..."
    kubectl wait --for=condition=Available deployment/nginx-load-balancer -n $NAMESPACE --timeout=300s
    
    # Get external IP
    log_info "Waiting for external IP assignment..."
    for i in {1..30}; do
        EXTERNAL_IP=$(kubectl get service nginx-load-balancer-service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
        if [[ -n "$EXTERNAL_IP" && "$EXTERNAL_IP" != "null" ]]; then
            log_success "Load balancer external IP: $EXTERNAL_IP"
            break
        fi
        echo "Waiting for external IP... ($i/30)"
        sleep 10
    done
    
    if [[ -z "$EXTERNAL_IP" || "$EXTERNAL_IP" == "null" ]]; then
        log_warning "External IP not assigned yet. Check load balancer status manually."
    fi
    
    log_success "Load balancer deployed successfully"
}

# Deploy monitoring
deploy_monitoring() {
    log_info "Deploying monitoring stack..."
    
    kubectl apply -f ../kubernetes/monitoring.yaml
    
    # Wait for monitoring to be ready
    log_info "Waiting for Prometheus to be ready..."
    kubectl wait --for=condition=Available deployment/prometheus -n $NAMESPACE --timeout=300s
    
    log_info "Waiting for Grafana to be ready..."
    kubectl wait --for=condition=Available deployment/grafana -n $NAMESPACE --timeout=300s
    
    log_success "Monitoring stack deployed successfully"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check all pods
    echo "Pod status:"
    kubectl get pods -n $NAMESPACE
    
    # Check services
    echo -e "\nService status:"
    kubectl get services -n $NAMESPACE
    
    # Check HPA
    echo -e "\nHorizontal Pod Autoscaler status:"
    kubectl get hpa -n $NAMESPACE
    
    # Check ingress
    echo -e "\nIngress status:"
    kubectl get ingress -n $NAMESPACE
    
    # Health check
    log_info "Performing health checks..."
    
    # Port forward for health check
    kubectl port-forward service/mental-health-backend-service 8080:8000 -n $NAMESPACE &
    PORT_FORWARD_PID=$!
    
    sleep 5
    
    if curl -f http://localhost:8080/api/monitoring/health &> /dev/null; then
        log_success "Backend health check passed"
    else
        log_warning "Backend health check failed"
    fi
    
    # Clean up port forward
    kill $PORT_FORWARD_PID 2>/dev/null || true
    
    log_success "Deployment verification completed"
}

# Scale deployment
scale_deployment() {
    local component=$1
    local replicas=$2
    
    log_info "Scaling $component to $replicas replicas..."
    
    kubectl scale deployment $component -n $NAMESPACE --replicas=$replicas
    kubectl wait --for=condition=Available deployment/$component -n $NAMESPACE --timeout=300s
    
    log_success "$component scaled successfully"
}

# Rollback deployment
rollback_deployment() {
    local component=$1
    
    log_info "Rolling back $component..."
    
    kubectl rollout undo deployment/$component -n $NAMESPACE
    kubectl rollout status deployment/$component -n $NAMESPACE
    
    log_success "$component rolled back successfully"
}

# Update deployment
update_deployment() {
    local component=$1
    local image=$2
    
    log_info "Updating $component with image $image..."
    
    kubectl set image deployment/$component $component=$image -n $NAMESPACE
    kubectl rollout status deployment/$component -n $NAMESPACE
    
    log_success "$component updated successfully"
}

# Cleanup deployment
cleanup_deployment() {
    log_warning "This will delete the entire Mental Health Agent deployment!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Cleanup cancelled"
        return
    fi
    
    log_info "Cleaning up deployment..."
    
    # Delete in reverse order
    kubectl delete -f ../kubernetes/monitoring.yaml --ignore-not-found=true
    kubectl delete -f ../kubernetes/load-balancer.yaml --ignore-not-found=true
    kubectl delete -f ../kubernetes/backend-deployment.yaml --ignore-not-found=true
    kubectl delete -f ../kubernetes/database-cluster.yaml --ignore-not-found=true
    kubectl delete -f ../kubernetes/configmap.yaml --ignore-not-found=true
    
    # Delete PVCs
    kubectl delete pvc --all -n $NAMESPACE
    
    # Delete namespace
    kubectl delete namespace $NAMESPACE --ignore-not-found=true
    
    log_success "Cleanup completed"
}

# Main deployment function
deploy_all() {
    log_info "Starting Mental Health Agent deployment..."
    
    check_prerequisites
    create_namespace
    deploy_secrets
    deploy_config
    deploy_databases
    deploy_backend
    deploy_load_balancer
    deploy_monitoring
    verify_deployment
    
    log_success "Mental Health Agent deployment completed successfully!"
    
    echo -e "\n${GREEN}Deployment Summary:${NC}"
    echo "- Namespace: $NAMESPACE"
    echo "- Backend replicas: $(kubectl get deployment mental-health-backend -n $NAMESPACE -o jsonpath='{.status.replicas}')"
    echo "- Load balancer replicas: $(kubectl get deployment nginx-load-balancer -n $NAMESPACE -o jsonpath='{.status.replicas}')"
    echo "- External IP: $(kubectl get service nginx-load-balancer-service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo 'Pending')"
    
    echo -e "\n${BLUE}Next Steps:${NC}"
    echo "1. Configure DNS to point to the external IP"
    echo "2. Set up SSL certificates"
    echo "3. Configure monitoring alerts"
    echo "4. Run load tests"
    echo "5. Set up backup procedures"
}

# Command line interface
case "${1:-deploy}" in
    "deploy")
        deploy_all
        ;;
    "scale")
        if [[ -z "$2" || -z "$3" ]]; then
            echo "Usage: $0 scale <component> <replicas>"
            echo "Example: $0 scale mental-health-backend 5"
            exit 1
        fi
        scale_deployment "$2" "$3"
        ;;
    "rollback")
        if [[ -z "$2" ]]; then
            echo "Usage: $0 rollback <component>"
            echo "Example: $0 rollback mental-health-backend"
            exit 1
        fi
        rollback_deployment "$2"
        ;;
    "update")
        if [[ -z "$2" || -z "$3" ]]; then
            echo "Usage: $0 update <component> <image>"
            echo "Example: $0 update mental-health-backend mental-health-agent/backend:v2.0"
            exit 1
        fi
        update_deployment "$2" "$3"
        ;;
    "verify")
        verify_deployment
        ;;
    "cleanup")
        cleanup_deployment
        ;;
    "help")
        echo "Mental Health Agent Kubernetes Deployment Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  deploy              Deploy the complete system (default)"
        echo "  scale <comp> <num>  Scale a component to specified replicas"
        echo "  rollback <comp>     Rollback a component to previous version"
        echo "  update <comp> <img> Update a component with new image"
        echo "  verify              Verify deployment status"
        echo "  cleanup             Remove the entire deployment"
        echo "  help                Show this help message"
        echo ""
        echo "Environment Variables:"
        echo "  KUBECTL_CONTEXT     Kubernetes context to use (default: production)"
        echo "  ENVIRONMENT         Deployment environment (default: production)"
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
