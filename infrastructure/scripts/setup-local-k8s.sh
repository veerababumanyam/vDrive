#!/bin/bash
# ===========================================
# Local Kubernetes Setup Script (k3d/minikube)
# ===========================================
# Sets up a local Kubernetes cluster for development

set -e

CLUSTER_NAME="RawDrive-dev"
K3D_VERSION="v5.6.0"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=============================================${NC}"
echo -e "${BLUE}RawDrive Local Kubernetes Setup${NC}"
echo -e "${BLUE}=============================================${NC}"

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     PLATFORM=linux;;
    Darwin*)    PLATFORM=darwin;;
    MINGW*|CYGWIN*|MSYS*) PLATFORM=windows;;
    *)          PLATFORM="unknown"
esac

echo -e "Detected platform: ${GREEN}$PLATFORM${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo -e "Please install Docker Desktop first"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}Error: Docker daemon is not running${NC}"
    echo -e "Please start Docker Desktop"
    exit 1
fi

echo -e "${GREEN}✓ Docker is running${NC}"

# Install k3d if not present
if ! command -v k3d &> /dev/null; then
    echo -e "\n${YELLOW}Installing k3d...${NC}"
    if [ "$PLATFORM" = "windows" ]; then
        echo -e "Please install k3d manually: https://k3d.io/"
        echo -e "Or run: choco install k3d"
        exit 1
    else
        curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash
    fi
fi

echo -e "${GREEN}✓ k3d is installed${NC}"

# Check if cluster exists
if k3d cluster list | grep -q "$CLUSTER_NAME"; then
    echo -e "\n${YELLOW}Cluster '$CLUSTER_NAME' already exists${NC}"
    read -p "Do you want to delete and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "Deleting existing cluster..."
        k3d cluster delete "$CLUSTER_NAME"
    else
        echo -e "Using existing cluster"
        kubectl config use-context "k3d-$CLUSTER_NAME"
        exit 0
    fi
fi

# Create k3d cluster
echo -e "\n${YELLOW}Creating k3d cluster...${NC}"
k3d cluster create "$CLUSTER_NAME" \
    --servers 1 \
    --agents 3 \
    --port "80:80@loadbalancer" \
    --port "443:443@loadbalancer" \
    --port "8080:8080@loadbalancer" \
    --port "5432:5432@loadbalancer" \
    --port "6379:6379@loadbalancer" \
    --port "9092:9092@loadbalancer" \
    --port "9090:9090@loadbalancer" \
    --port "3001:3001@loadbalancer" \
    --k3s-arg "--disable=traefik@server:0" \
    --volume "$(pwd)/infrastructure:/infrastructure@all" \
    --wait

echo -e "${GREEN}✓ Cluster created${NC}"

# Set kubectl context
kubectl config use-context "k3d-$CLUSTER_NAME"

# Create RawDrive namespace
echo -e "\n${YELLOW}Creating RawDrive namespace...${NC}"
kubectl create namespace RawDrive --dry-run=client -o yaml | kubectl apply -f -

# Install KEDA
echo -e "\n${YELLOW}Installing KEDA...${NC}"
kubectl apply -f https://github.com/kedacore/keda/releases/download/v2.12.0/keda-2.12.0.yaml
kubectl wait --for=condition=available --timeout=120s deployment/keda-operator -n keda

# Install Traefik CRDs
echo -e "\n${YELLOW}Installing Traefik CRDs...${NC}"
kubectl apply -f https://raw.githubusercontent.com/traefik/traefik/v3.0/docs/content/reference/dynamic-configuration/kubernetes-crd-definition-v1.yml

# Install metrics server (for HPA/KEDA)
echo -e "\n${YELLOW}Installing metrics server...${NC}"
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml 2>/dev/null || true

echo -e "\n${GREEN}=============================================${NC}"
echo -e "${GREEN}Local Kubernetes Setup Complete!${NC}"
echo -e "${GREEN}=============================================${NC}"

echo -e "\n${YELLOW}Cluster Info:${NC}"
kubectl cluster-info

echo -e "\n${YELLOW}Nodes:${NC}"
kubectl get nodes

echo -e "\n${BLUE}Next Steps:${NC}"
echo -e "  1. Deploy RawDrive: ./infrastructure/scripts/deploy-k8s.sh dev"
echo -e "  2. Access services via localhost ports"
echo -e "  3. Delete cluster: k3d cluster delete $CLUSTER_NAME"

echo -e "\n${BLUE}Port Mappings:${NC}"
echo -e "  HTTP:       localhost:80"
echo -e "  HTTPS:      localhost:443"
echo -e "  Traefik:    localhost:8080"
echo -e "  PostgreSQL: localhost:5432"
echo -e "  Redis:      localhost:6379"
echo -e "  Kafka:      localhost:9092"
echo -e "  Prometheus: localhost:9090"
echo -e "  Grafana:    localhost:3001"
