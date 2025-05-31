#!/bin/bash

# fix-permissions.sh - Fix file permissions for Docker Compose

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

print_info "Fixing permissions for Docker Compose..."

# Get current user ID and group ID
CURRENT_UID=$(id -u)
CURRENT_GID=$(id -g)

print_info "Current UID: $CURRENT_UID, GID: $CURRENT_GID"

# Create or update .env file with UID/GID
if [[ -f ".env" ]]; then
    # Remove existing UID/GID lines
    sed -i '/^UID=/d' .env
    sed -i '/^GID=/d' .env
else
    # Create .env from sample if it doesn't exist
    if [[ -f "env.sample" ]]; then
        cp env.sample .env
        print_info "Created .env from env.sample"
    else
        touch .env
        print_info "Created empty .env file"
    fi
fi

# Add UID/GID to .env
echo "UID=$CURRENT_UID" >> .env
echo "GID=$CURRENT_GID" >> .env
print_success "Added UID/GID to .env file"

# Fix permissions on directories
print_info "Fixing directory permissions..."
chmod 755 reports cache 2>/dev/null || mkdir -p reports cache && chmod 755 reports cache
print_success "Fixed reports and cache directory permissions"

# Fix permissions on credentials
if [[ -d "credentials" ]]; then
    print_info "Fixing credentials directory permissions..."
    chmod 755 credentials
    if [[ -f "credentials/application_default_credentials.json" ]]; then
        chmod 644 credentials/application_default_credentials.json
        print_success "Fixed credentials file permissions"
    fi
else
    print_warning "credentials directory not found"
fi

# Fix permissions on gcloud directory
if [[ -d "gcloud" ]]; then
    print_info "Fixing gcloud directory permissions..."
    chmod -R 755 gcloud
    if [[ -f "gcloud/application_default_credentials.json" ]]; then
        chmod 644 gcloud/application_default_credentials.json
        print_success "Fixed gcloud credentials file permissions"
    fi
else
    print_warning "gcloud directory not found"
fi

print_success "Permission fixes completed!"
print_info "You can now run: docker compose run --rm recon-ai-agent python main.py -d testphp.vulnweb.com" 