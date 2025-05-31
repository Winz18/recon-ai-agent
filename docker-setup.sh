#!/bin/bash

# docker-setup.sh - Setup script for Recon AI-Agent Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
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

print_info "Setting up Recon AI-Agent Docker Compose environment..."

# Create necessary directories
print_info "Creating necessary directories..."
mkdir -p reports cache credentials gcloud

# Check if .env file exists
if [[ ! -f ".env" ]]; then
    if [[ -f "env.sample" ]]; then
        print_info "Creating .env file from sample..."
        cp env.sample .env
        print_warning "Please edit .env file and add your Google Cloud Project ID and Region"
        print_info "Required variables:"
        echo "  - GOOGLE_PROJECT_ID: Your Google Cloud Project ID"
        echo "  - GOOGLE_REGION: Your preferred Google Cloud region (default: us-central1)"
    else
        print_warning ".env file not found and no sample available"
        print_info "Creating basic .env file..."
        cat > .env << EOF
# Google Cloud Configuration
GOOGLE_PROJECT_ID=your-google-project-id
GOOGLE_REGION=us-central1
TARGET_DOMAIN=google.com
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/application_default_credentials.json
EOF
        print_warning "Please edit .env file and add your actual Google Cloud Project ID"
    fi
else
    print_success ".env file already exists"
fi

# Check for Google Cloud credentials
if [[ ! -f "credentials/application_default_credentials.json" ]] && [[ ! -f "gcloud/application_default_credentials.json" ]]; then
    print_warning "No Google Cloud credentials found"
    print_info "You have two options for authentication:"
    echo "  1. Use Application Default Credentials:"
    echo "     gcloud auth application-default login"
    echo "  2. Place service account key in:"
    echo "     credentials/application_default_credentials.json"
else
    print_success "Google Cloud credentials found"
fi

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker compose &> /dev/null && ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_success "Docker and Docker Compose are available"

# Test docker-compose configuration
print_info "Validating docker-compose configuration..."
if docker compose config > /dev/null 2>&1; then
    print_success "docker-compose.yml is valid"
else
    print_error "docker-compose.yml validation failed"
    exit 1
fi

print_success "Setup completed successfully!"
print_info "Next steps:"
echo "  1. Edit .env file with your Google Cloud Project ID"
echo "  2. Ensure Google Cloud authentication is configured"
echo "  3. Run: docker compose up --build"
echo "  4. Or use: ./docker-run.sh -d example.com" 