#!/bin/bash

# Deploy Script for Big Data Project
# This script checks prerequisites and deploys the project stack

set -e  # Exit on any error

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Docker installation and status
check_docker() {
    log_info "Checking Docker installation..."
    
    if ! command_exists docker; then
        log_error "Docker is not installed. Please install Docker first."
        log_error "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    log_success "Docker is installed"
    
    # Check if Docker daemon is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon is not running. Please start Docker first."
        log_error "Run: sudo systemctl start docker"
        exit 1
    fi
    
    log_success "Docker daemon is running"
    
    # Display Docker version
    DOCKER_VERSION=$(docker --version)
    log_info "Docker version: $DOCKER_VERSION"
}

# Function to check Docker Compose installation
check_docker_compose() {
    log_info "Checking Docker Compose installation..."
    
    # Check for docker-compose command
    if command_exists docker-compose; then
        COMPOSE_CMD="docker-compose"
        log_success "Docker Compose is installed (standalone)"
    # Check for docker compose plugin
    elif docker compose version >/dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
        log_success "Docker Compose is installed (plugin)"
    else
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        log_error "Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    # Display Docker Compose version
    COMPOSE_VERSION=$($COMPOSE_CMD --version)
    log_info "Docker Compose version: $COMPOSE_VERSION"
}

# Function to validate docker-compose.yaml file
validate_compose_file() {
    log_info "Validating docker-compose.yaml file..."
    
    if [ ! -f "docker-compose.yaml" ]; then
        log_error "docker-compose.yaml file not found in current directory"
        exit 1
    fi
    
    # Validate compose file syntax
    if ! $COMPOSE_CMD config >/dev/null 2>&1; then
        log_error "docker-compose.yaml file has syntax errors"
        log_error "Run '$COMPOSE_CMD config' to see detailed errors"
        exit 1
    fi
    
    log_success "docker-compose.yaml file is valid"
}

# Function to pull Docker images
pull_images() {
    log_info "Pulling Docker images..."
    log_info "This may take several minutes..."
    
    if ! $COMPOSE_CMD pull; then
        log_error "Failed to pull Docker images"
        log_error "Check your internet connection and Docker registry access"
        exit 1
    fi
    
    log_success "All Docker images pulled successfully"
}

# Function to start services
start_services() {
    log_info "Starting all services with Docker Compose..."
    
    if ! $COMPOSE_CMD up -d; then
        log_error "Failed to start services"
        log_error "Check the logs with: $COMPOSE_CMD logs in another terminal"
        exit 1
    fi
    
    log_success "All services started successfully"
}

# Function to display container status
show_container_status() {
    log_info "Current container status:"
    echo
    docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo
    
    # Count running containers
    RUNNING_CONTAINERS=$(docker ps -q | wc -l)
    TOTAL_CONTAINERS=$(docker ps -aq | wc -l)
    
    log_info "Containers: $RUNNING_CONTAINERS running, $TOTAL_CONTAINERS total"
}

# Function to display service URLs
show_service_urls() {
    log_info "Service URLs (replace localhost with your server IP if accessing remotely):"
    echo
    echo -e "${GREEN}📊 Dashboard UI:${NC}            http://localhost:3000"
    echo -e "${GREEN}📋 Apache Kafka UI:${NC}         http://localhost:8088"
    echo -e "${GREEN}📈 Apache Flink Dashboard:${NC}  http://localhost:8081"
    echo -e "${GREEN}💾 InfluxDB UI:${NC}             http://localhost:8086"
    echo
}

# Function to show helpful commands
show_helpful_commands() {
    log_info "Helpful commands:"
    echo
    echo "View logs:           $COMPOSE_CMD logs -f"
    echo "View specific logs:  $COMPOSE_CMD logs -f <service-name>"
    echo "Restart service:     $COMPOSE_CMD restart <service-name>"
    echo "Check status:        $COMPOSE_CMD ps"
    echo
}

# Main deployment function
main() {
    echo
    log_info "Starting Big Data Project Deployment..."
    echo
    
    # Step 1: Check prerequisites
    check_docker
    check_docker_compose
    validate_compose_file
    
    echo
    log_info "All prerequisites met! Proceeding with deployment..."
    echo
    
    # Step 2: Pull images
    pull_images
    
    echo
    
    # Step 3: Start services
    start_services
    
    echo
    
    # Step 4: Show status
    show_container_status
    log_info "It may take a few minutes for all services to be fully ready."
    
    echo

    # Step 5: Show helpful info
    show_helpful_commands

    echo
    
    # Step 6: Show URLs
    show_service_urls

    log_success "Big Data Project Deployment Completed Successfully! 🚀"
}

# Trap to handle script interruption
trap 'log_error "Deployment interrupted by user"; exit 1' INT TERM

# Check if script is run from correct directory
if [ ! -f "docker-compose.yaml" ]; then
    log_error "Please run this script from the project root directory (where docker-compose.yaml is located)"
    exit 1
fi

# Run main function
main
