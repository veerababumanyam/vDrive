#!/bin/bash
# ===========================================
# RawDrive Kubernetes Deployment Script
# ===========================================
# Usage: ./deploy-k8s.sh [dev|staging|prod]

set -e

ENVIRONMENT=${1:-dev}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(dirname "$SCRIPT_DIR")"
K8S_DIR="$INFRA_DIR/kubernetes"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=============================================${NC}"
echo -e "${BLUE}RawDrive Kubernetes Deployment${NC}"
echo -e "${BLUE}Environment: ${GREEN}$ENVIRONMENT${NC}"
echo -e "${BLUE}=============================================${NC}"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    echo -e "${RED}Error: Invalid environment. Use: dev, staging, or prod${NC}"
    exit 1
fi

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl is not installed${NC}"
    exit 1
fi

if ! command -v kustomize &> /dev/null; then
    echo -e "${YELLOW}Warning: kustomize CLI not found, using kubectl's built-in kustomize${NC}"
fi

# Check cluster connection
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}Error: Cannot connect to Kubernetes cluster${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}"

# Install KEDA if not present
echo -e "\n${YELLOW}Checking KEDA installation...${NC}"
if ! kubectl get crd scaledobjects.keda.sh &> /dev/null; then
    echo -e "${YELLOW}Installing KEDA...${NC}"
    kubectl apply -f https://github.com/kedacore/keda/releases/download/v2.12.0/keda-2.12.0.yaml
    echo -e "${GREEN}✓ KEDA installed${NC}"
    echo -e "${YELLOW}Waiting for KEDA to be ready...${NC}"
    kubectl wait --for=condition=available --timeout=120s deployment/keda-operator -n keda
else
    echo -e "${GREEN}✓ KEDA already installed${NC}"
fi

# Install Traefik CRDs if not present
echo -e "\n${YELLOW}Checking Traefik CRDs...${NC}"
if ! kubectl get crd ingressroutes.traefik.io &> /dev/null; then
    echo -e "${YELLOW}Installing Traefik CRDs...${NC}"
    kubectl apply -f https://raw.githubusercontent.com/traefik/traefik/v3.0/docs/content/reference/dynamic-configuration/kubernetes-crd-definition-v1.yml
    echo -e "${GREEN}✓ Traefik CRDs installed${NC}"
else
    echo -e "${GREEN}✓ Traefik CRDs already installed${NC}"
fi

# Deploy using Kustomize
OVERLAY_DIR="$K8S_DIR/overlays/$ENVIRONMENT"

echo -e "\n${YELLOW}Deploying to $ENVIRONMENT environment...${NC}"
echo -e "Using overlay: $OVERLAY_DIR"

# Dry run first
echo -e "\n${YELLOW}Running dry-run validation...${NC}"
kubectl apply -k "$OVERLAY_DIR" --dry-run=client
echo -e "${GREEN}✓ Validation passed${NC}"

# Apply the configuration
echo -e "\n${YELLOW}Applying configuration...${NC}"
kubectl apply -k "$OVERLAY_DIR"

# Wait for core services
echo -e "\n${YELLOW}Waiting for core services...${NC}"

PREFIX="${ENVIRONMENT}-"

# Wait for PostgreSQL
echo -e "  Waiting for PostgreSQL..."
kubectl wait --for=condition=ready pod -l app=postgres -n RawDrive --timeout=300s 2>/dev/null || true

# Wait for Redis
echo -e "  Waiting for Redis..."
kubectl wait --for=condition=ready pod -l app=redis -n RawDrive --timeout=120s 2>/dev/null || true

# Wait for Kafka
echo -e "  Waiting for Kafka..."
kubectl wait --for=condition=ready pod -l app=kafka -n RawDrive --timeout=180s 2>/dev/null || true

# Wait for Traefik
echo -e "  Waiting for Traefik..."
kubectl wait --for=condition=available deployment/${PREFIX}traefik -n RawDrive --timeout=120s 2>/dev/null || true

# Wait for Backend
echo -e "  Waiting for Backend..."
kubectl wait --for=condition=available deployment/${PREFIX}backend -n RawDrive --timeout=180s 2>/dev/null || true

echo -e "\n${GREEN}=============================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}=============================================${NC}"

# Show status
echo -e "\n${YELLOW}Deployment Status:${NC}"
kubectl get pods -n RawDrive -o wide

echo -e "\n${YELLOW}Services:${NC}"
kubectl get svc -n RawDrive

echo -e "\n${YELLOW}Ingress Routes:${NC}"
kubectl get ingressroutes -n RawDrive 2>/dev/null || echo "No IngressRoutes found"

echo -e "\n${YELLOW}KEDA ScaledObjects:${NC}"
kubectl get scaledobjects -n RawDrive 2>/dev/null || echo "No ScaledObjects found"

# Get Traefik LoadBalancer IP
echo -e "\n${YELLOW}Access Information:${NC}"
TRAEFIK_IP=$(kubectl get svc ${PREFIX}traefik -n RawDrive -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
if [ "$TRAEFIK_IP" != "pending" ] && [ -n "$TRAEFIK_IP" ]; then
    echo -e "  Traefik LoadBalancer IP: ${GREEN}$TRAEFIK_IP${NC}"
    echo -e "  API URL: ${GREEN}http://$TRAEFIK_IP/api/v1${NC}"
else
    echo -e "  Traefik LoadBalancer: ${YELLOW}Pending (use 'kubectl get svc -n RawDrive' to check)${NC}"
fi

echo -e "\n${BLUE}Useful Commands:${NC}"
echo -e "  View logs:     kubectl logs -f deployment/${PREFIX}backend -n RawDrive"
echo -e "  Port forward:  kubectl port-forward svc/${PREFIX}backend 8000:8000 -n RawDrive"
echo -e "  Scale:         kubectl scale deployment/${PREFIX}backend --replicas=5 -n RawDrive"
echo -e "  Delete all:    kubectl delete -k $OVERLAY_DIR"
