#!/bin/bash

# Mini RAG Docker Startup Script
# This script starts the complete RAG system with Qdrant, FastAPI app, and web UI

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is available
port_available() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1
    else
        return 0
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            print_success "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start within expected time"
    return 1
}

# Function to confirm action
confirm() {
    local message=$1
    echo -n "$message (y/N): "
    read -r response
    case "$response" in
        [yY][eE][sS]|[yY])
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Main startup sequence
main() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    Mini RAG Docker Startup                  ║"
    echo "║                                                              ║"
    echo "║  🚀 Starting complete RAG system with:                      ║"
    echo "║     • Qdrant Vector Database                                 ║"
    echo "║     • FastAPI RAG Application                               ║"
    echo "║     • Beautiful Web UI                                      ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    # Check prerequisites
    print_status "Checking prerequisites..."
    
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker Desktop first."
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker Desktop first."
        exit 1
    fi
    
    print_success "Docker environment is ready"
    
    # Check if ports are available
    print_status "Checking port availability..."
    
    if ! port_available 6333; then
        print_warning "Port 6333 (Qdrant) is already in use"
        if ! confirm "Do you want to continue anyway?"; then
            exit 1
        fi
    fi
    
    if ! port_available 8000; then
        print_warning "Port 8000 (RAG API) is already in use"
        if ! confirm "Do you want to continue anyway?"; then
            exit 1
        fi
    fi
    
    if ! port_available 80; then
        print_warning "Port 80 (Nginx) is already in use"
        if ! confirm "Do you want to continue anyway?"; then
            exit 1
        fi
    fi
    
    print_success "Ports are available"
    
    # Check if Ollama is running
    print_status "Checking Ollama connection..."
    if ! curl -s "http://localhost:11434/api/tags" >/dev/null 2>&1; then
        print_warning "Ollama is not running on localhost:11434"
        print_status "Make sure Ollama is running and has the required models:"
        echo "  • llama3.1:8b (for text generation)"
        echo "  • nomic-embed-text (for embeddings)"
        echo ""
        if ! confirm "Do you want to continue anyway?"; then
            exit 1
        fi
    else
        print_success "Ollama is running"
    fi
    
    # Build and start services
    print_status "Building and starting services..."
    
    # Stop any existing services
    if docker-compose ps | grep -q "mini-rag"; then
        print_status "Stopping existing services..."
        docker-compose down
    fi
    
    # Build the application
    print_status "Building RAG application..."
    docker-compose build rag-app
    
    # Start all services
    print_status "Starting services..."
    docker-compose up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to start..."
    
    # Wait for Qdrant
    if ! wait_for_service "http://localhost:6333/health" "Qdrant"; then
        print_error "Failed to start Qdrant"
        docker-compose logs qdrant
        exit 1
    fi
    
    # Wait for RAG API
    if ! wait_for_service "http://localhost:8000/health" "RAG API"; then
        print_error "Failed to start RAG API"
        docker-compose logs rag-app
        exit 1
    fi
    
    # Check service status
    print_status "Checking service status..."
    docker-compose ps
    
    # Display access information
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    🎉 System Ready! 🎉                      ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}🌐 Web Interface:${NC} http://localhost:8000"
    echo -e "${BLUE}📚 API Documentation:${NC} http://localhost:8000/docs"
    echo -e "${BLUE}🔍 Health Check:${NC} http://localhost:8000/health"
    echo -e "${BLUE}🗄️  Qdrant Dashboard:${NC} http://localhost:6333/dashboard"
    echo ""
    echo -e "${BLUE}📖 Quick Start:${NC}"
    echo "  1. Open http://localhost:8000 in your browser"
    echo "  2. Upload some documents (PDF, MD, TXT)"
    echo "  3. Ask questions about your documents!"
    echo ""
    echo -e "${BLUE}🛑 To stop services:${NC} docker-compose down"
    echo -e "${BLUE}📋 View logs:${NC} docker-compose logs -f"
    echo ""
    
    # Optional: Open web UI in browser
    if command_exists open; then
        if confirm "Would you like to open the web UI in your browser?"; then
            open "http://localhost:8000"
        fi
    fi
}

# Handle script interruption
trap 'echo -e "\n${YELLOW}[WARNING]${NC} Startup interrupted"; exit 1' INT TERM

# Run main function
main "$@" 