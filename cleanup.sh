#!/bin/bash

# Cleanup Script for Big Data Project
# This script stops and cleans up the project stack

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default flags
CLEANUP_VOLUMES=false
CLEANUP_IMAGES=false
CLEANUP_NETWORKS=false
FORCE_CLEANUP=false

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

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  --volumes, -v        Remove Docker volumes (data will be lost!)"
    echo "  --images, -i         Remove Docker images to save space"
    echo "  --networks, -n       Remove Docker networks"
    echo "  --all, -a            Remove everything (volumes, images, networks)"
    echo "  --force, -f          Skip confirmation prompts"
    echo "  --help, -h           Show this help message"
    echo
    echo "Examples:"
    echo "  $0                   Basic cleanup (stop containers only)"
    echo "  $0 --volumes         Stop containers and remove volumes"
    echo "  $0 --all --force     Remove everything without prompts"
}

# Function to parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --volumes|-v)
                CLEANUP_VOLUMES=true
                shift
                ;;
            --images|-i)
                CLEANUP_IMAGES=true
                shift
                ;;
            --networks|-n)
                CLEANUP_NETWORKS=true
                shift
                ;;
            --all|-a)
                CLEANUP_VOLUMES=true
                CLEANUP_IMAGES=true
                CLEANUP_NETWORKS=true
                shift
                ;;
            --force|-f)
                FORCE_CLEANUP=true
                shift
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect Docker Compose command
detect_compose_command() {
    if command_exists docker-compose; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version >/dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
    else
        log_error "Docker Compose is not available"
        exit 1
    fi
}

# Function to confirm destructive actions
confirm_action() {
    local message="$1"
    
    if [ "$FORCE_CLEANUP" = true ]; then
        return 0
    fi
    
    echo
    log_warning "$message"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Operation cancelled by user"
        return 1
    fi
    
    return 0
}

# Function to stop and remove containers
stop_services() {
    log_info "Stopping all services..."
    
    if [ ! -f "docker-compose.yaml" ]; then
        log_error "docker-compose.yaml file not found in current directory"
        exit 1
    fi
    
    # Check if any containers are running
    if ! $COMPOSE_CMD ps -q | grep -q .; then
        log_info "No containers are currently running"
        return 0
    fi
    
    # Stop and remove containers
    if ! $COMPOSE_CMD down; then
        log_error "Failed to stop services"
        exit 1
    fi
    
    log_success "All services stopped and containers removed"
}

# Function to remove volumes
cleanup_volumes() {
    if [ "$CLEANUP_VOLUMES" != true ]; then
        return 0
    fi
    
    if ! confirm_action "This will delete all data volumes. All stored data will be permanently lost!"; then
        return 0
    fi
    
    log_info "Removing Docker volumes..."
    
    # Get project volumes
    PROJECT_VOLUMES=$($COMPOSE_CMD config --volumes 2>/dev/null || echo "")
    
    if [ -z "$PROJECT_VOLUMES" ]; then
        log_info "No project volumes found"
        return 0
    fi
    
    # Remove volumes with error handling
    echo "$PROJECT_VOLUMES" | while read -r volume; do
        if [ -n "$volume" ]; then
            if docker volume rm "${PWD##*/}_$volume" 2>/dev/null; then
                log_success "Removed volume: ${PWD##*/}_$volume"
            else
                log_warning "Volume not found or already removed: ${PWD##*/}_$volume"
            fi
        fi
    done
    
    # Also try to remove volumes by project name pattern
    PROJECT_NAME=$(basename "$PWD" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]//g')
    VOLUMES_TO_REMOVE=$(docker volume ls -q | grep "^${PROJECT_NAME}" || true)
    
    if [ -n "$VOLUMES_TO_REMOVE" ]; then
        echo "$VOLUMES_TO_REMOVE" | while read -r volume; do
            if docker volume rm "$volume" 2>/dev/null; then
                log_success "Removed volume: $volume"
            fi
        done
    fi
    
    log_success "Volume cleanup completed"
}

# Function to remove images
cleanup_images() {
    if [ "$CLEANUP_IMAGES" != true ]; then
        return 0
    fi
    
    if ! confirm_action "This will remove Docker images. You'll need to pull them again on next deployment."; then
        return 0
    fi
    
    log_info "Removing Docker images..."
    
    # Get images used by the project
    IMAGES=$($COMPOSE_CMD config | grep "image:" | sed 's/.*image: *//' | sort -u || echo "")
    
    if [ -z "$IMAGES" ]; then
        log_info "No project images found"
        return 0
    fi
    
    # Remove images
    echo "$IMAGES" | while read -r image; do
        if [ -n "$image" ]; then
            if docker rmi "$image" 2>/dev/null; then
                log_success "Removed image: $image"
            else
                log_warning "Image not found or in use: $image"
            fi
        fi
    done
    
    log_success "Image cleanup completed"
}

# Function to remove networks
cleanup_networks() {
    if [ "$CLEANUP_NETWORKS" != true ]; then
        return 0
    fi
    
    log_info "Removing Docker networks..."
    
    # Get project networks
    PROJECT_NAME=$(basename "$PWD" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]//g')
    NETWORKS_TO_REMOVE=$(docker network ls --format "{{.Name}}" | grep "^${PROJECT_NAME}" || true)
    
    if [ -z "$NETWORKS_TO_REMOVE" ]; then
        log_info "No project networks found"
        return 0
    fi
    
    # Remove networks
    echo "$NETWORKS_TO_REMOVE" | while read -r network; do
        if [ -n "$network" ]; then
            if docker network rm "$network" 2>/dev/null; then
                log_success "Removed network: $network"
            else
                log_warning "Network not found or in use: $network"
            fi
        fi
    done
    
    log_success "Network cleanup completed"
}

# Function to clean up orphaned resources
cleanup_orphaned_resources() {
    log_info "Cleaning up orphaned Docker resources..."
    
    # Remove stopped containers
    STOPPED_CONTAINERS=$(docker ps -aq --filter "status=exited" || true)
    if [ -n "$STOPPED_CONTAINERS" ]; then
        docker rm $STOPPED_CONTAINERS >/dev/null 2>&1 || true
        log_success "Removed stopped containers"
    fi
    
    # Remove dangling images
    DANGLING_IMAGES=$(docker images -q --filter "dangling=true" || true)
    if [ -n "$DANGLING_IMAGES" ]; then
        docker rmi $DANGLING_IMAGES >/dev/null 2>&1 || true
        log_success "Removed dangling images"
    fi
    
    # Remove unused networks
    docker network prune -f >/dev/null 2>&1 || true
    
    log_success "Orphaned resources cleanup completed"
}

# Function to display cleanup summary
show_cleanup_summary() {
    log_info "Cleanup Summary:"
    echo
    
    # Show current Docker resource usage
    echo "Current Docker resource usage:"
    docker system df 2>/dev/null || log_warning "Could not retrieve Docker system information"
    echo
    
    # Show running containers
    RUNNING_CONTAINERS=$(docker ps -q | wc -l | tr -d ' ')
    echo "Running containers: $RUNNING_CONTAINERS"
    
    # Show volumes
    TOTAL_VOLUMES=$(docker volume ls -q | wc -l | tr -d ' ')
    echo "Total volumes: $TOTAL_VOLUMES"
    
    # Show images
    TOTAL_IMAGES=$(docker images -q | wc -l | tr -d ' ')
    echo "Total images: $TOTAL_IMAGES"
    
    echo
}

# Function to show helpful commands
show_helpful_commands() {
    log_info "Helpful commands:"
    echo
    echo "View Docker usage:   docker system df"
    echo "Remove all stopped:  docker container prune"
    echo "Remove unused data:  docker system prune"
    echo "Remove everything:   docker system prune --all --volumes"
    echo "Restart deployment: ./deploy.sh"
    echo
}

# Main cleanup function
main() {
    echo
    log_info "Starting Big Data Project Cleanup..."
    echo
    
    # Parse command line arguments
    parse_arguments "$@"
    
    # Detect Docker Compose command
    detect_compose_command
    
    # Show what will be cleaned up
    log_info "Cleanup plan:"
    echo "  - Stop and remove containers: ✅"
    echo "  - Remove volumes: $([ "$CLEANUP_VOLUMES" = true ] && echo "✅" || echo "❌")"
    echo "  - Remove images: $([ "$CLEANUP_IMAGES" = true ] && echo "✅" || echo "❌")"
    echo "  - Remove networks: $([ "$CLEANUP_NETWORKS" = true ] && echo "✅" || echo "❌")"
    echo "  - Force mode: $([ "$FORCE_CLEANUP" = true ] && echo "✅" || echo "❌")"
    echo
    
    # Step 1: Stop services
    stop_services
    
    # Step 2: Clean up volumes
    cleanup_volumes
    
    # Step 3: Clean up images
    cleanup_images
    
    # Step 4: Clean up networks
    cleanup_networks
    
    # Step 5: Clean up orphaned resources
    cleanup_orphaned_resources
    
    echo
    
    # Step 6: Show summary
    show_cleanup_summary
    show_helpful_commands
    
    log_success "Cleanup completed successfully!"
    echo
}

# Trap to handle script interruption
trap 'log_error "Cleanup interrupted by user"; exit 1' INT TERM

# Check if script is run from correct directory
if [ ! -f "docker-compose.yaml" ]; then
    log_error "Please run this script from the project root directory (where docker-compose.yaml is located)"
    exit 1
fi

# Run main function with all arguments
main "$@"
