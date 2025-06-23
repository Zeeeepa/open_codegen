#!/bin/bash

# Enhanced OpenAI Codegen Adapter Startup Script
# This script:
# 1. Finds and upgrades the codegen package
# 2. Sets up the precise package location
# 3. Starts the backend server
# 4. Serves the frontend UI
# Web UI will be available at: http://localhost:8000

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Path to Python executable (try to detect automatically)
PYTHON_PATH=""
CODEGEN_PACKAGE_PATH=""
SERVER_PORT=8000

log_info "Starting Enhanced OpenAI Codegen Adapter Setup..."

# Try to find Python executable
if command -v python3 &> /dev/null; then
    PYTHON_PATH="python3"
elif command -v python &> /dev/null; then
    PYTHON_PATH="python"
elif [ -f "/home/l/.pyenv/versions/3.13.0/bin/python" ]; then
    PYTHON_PATH="/home/l/.pyenv/versions/3.13.0/bin/python"
else
    log_error "Python executable not found. Please install Python 3.7+ or update PYTHON_PATH in this script."
    exit 1
fi

log_success "Using Python: $PYTHON_PATH"

# Check Python version
PYTHON_VERSION=$($PYTHON_PATH --version 2>&1 | cut -d' ' -f2)
log_info "Python version: $PYTHON_VERSION"

# Function to find codegen package
find_codegen_package() {
    log_info "Searching for codegen package..."
    
    # Try to find codegen package in various locations
    local package_locations=(
        "$($PYTHON_PATH -c 'import site; print(site.getsitepackages()[0])' 2>/dev/null)/codegen"
        "$($PYTHON_PATH -c 'import site; print(site.getusersitepackages())' 2>/dev/null)/codegen"
        "$($PYTHON_PATH -m pip show codegen 2>/dev/null | grep Location | cut -d' ' -f2)/codegen"
    )
    
    for location in "${package_locations[@]}"; do
        if [ -d "$location" ] && [ -f "$location/__init__.py" ]; then
            CODEGEN_PACKAGE_PATH="$location"
            log_success "Found codegen package at: $CODEGEN_PACKAGE_PATH"
            return 0
        fi
    done
    
    log_warning "Codegen package not found in standard locations"
    return 1
}

# Function to install/upgrade codegen package
install_upgrade_codegen() {
    log_info "Installing/upgrading codegen package..."
    
    # Check if pip is available
    if ! $PYTHON_PATH -m pip --version &> /dev/null; then
        log_error "pip is not available. Please install pip first."
        exit 1
    fi
    
    # Try to upgrade codegen package
    if $PYTHON_PATH -m pip install --upgrade codegen &> /dev/null; then
        log_success "Codegen package upgraded successfully"
    else
        log_warning "Failed to upgrade codegen package, trying to install..."
        if $PYTHON_PATH -m pip install codegen &> /dev/null; then
            log_success "Codegen package installed successfully"
        else
            log_error "Failed to install codegen package. Please install manually."
            exit 1
        fi
    fi
}

# Function to setup environment
setup_environment() {
    log_info "Setting up environment..."
    
    # Set Python path to include current directory
    export PYTHONPATH=".:$PYTHONPATH"
    
    # Set codegen package location if found
    if [ -n "$CODEGEN_PACKAGE_PATH" ]; then
        export CODEGEN_SDK_PATH="$CODEGEN_PACKAGE_PATH"
        log_success "Codegen SDK path set to: $CODEGEN_SDK_PATH"
    fi
    
    # Set default credentials if not provided
    if [ -z "$CODEGEN_ORG_ID" ]; then
        export CODEGEN_ORG_ID="323"
        log_info "Using default CODEGEN_ORG_ID: $CODEGEN_ORG_ID"
    fi
    
    if [ -z "$CODEGEN_TOKEN" ]; then
        export CODEGEN_TOKEN="sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99"
        log_info "Using default CODEGEN_TOKEN"
    fi
}

# Function to validate project structure
validate_project_structure() {
    log_info "Validating project structure..."
    
    # Check if backend server exists
    if [ ! -f "backend/server.py" ]; then
        log_error "backend/server.py not found. Please ensure the project is properly structured."
        exit 1
    fi
    
    # Check if UI files exist
    if [ ! -f "src/index.html" ]; then
        log_error "src/index.html not found. Please ensure the project is properly structured."
        exit 1
    fi
    
    log_success "Project structure validated"
}

# Function to start the server
start_server() {
    log_info "Starting OpenAI Codegen Adapter server..."
    log_info "📊 Web UI will be available at: http://localhost:$SERVER_PORT"
    log_info "🔧 API endpoints will intercept OpenAI API calls and redirect to Codegen SDK"
    log_info "🎯 System Message functionality available in UI"
    echo ""
    
    # Start the server with proper configuration
    log_info "Executing: PYTHONPATH=. $PYTHON_PATH backend/server.py --port $SERVER_PORT"
    exec "$PYTHON_PATH" backend/server.py --port "$SERVER_PORT"
}

# Main execution flow
main() {
    # Find codegen package
    if ! find_codegen_package; then
        log_warning "Codegen package not found, attempting to install/upgrade..."
        install_upgrade_codegen
        find_codegen_package || log_warning "Could not locate codegen package after installation"
    else
        log_info "Attempting to upgrade existing codegen package..."
        install_upgrade_codegen
    fi
    
    # Setup environment
    setup_environment
    
    # Validate project structure
    validate_project_structure
    
    # Start the server
    start_server
}

# Handle script interruption
trap 'log_warning "Script interrupted. Cleaning up..."; exit 130' INT TERM

# Run main function
main "$@"
