#!/bin/bash

# docker-run.sh - Convenient script to run Recon AI-Agent with Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Default values
DOMAIN=""
WORKFLOW="standard"
OUTPUT_FORMAT="markdown"
VERBOSITY="1"
MODEL="gemini-2.5-pro-preview-05-06"

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -d, --domain DOMAIN       Target domain to scan (required)"
    echo "  -w, --workflow WORKFLOW   Workflow type (default: standard)"
    echo "                           Options: standard, quick, deep, targeted, stealth, comprehensive"
    echo "  -o, --output FORMAT       Output format (default: markdown)"
    echo "                           Options: markdown, html, json"
    echo "  -v, --verbosity LEVEL     Verbosity level 0-3 (default: 1)"
    echo "  -m, --model MODEL         AI model to use (default: gemini-2.5-pro-preview-05-06)"
    echo "  --build                   Build Docker image before running"
    echo "  --interactive             Run in interactive mode"
    echo "  -h, --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -d example.com"
    echo "  $0 -d example.com -w comprehensive -o html"
    echo "  $0 -d example.com -w stealth -v 2"
    echo "  $0 --build -d example.com"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--domain)
            DOMAIN="$2"
            shift 2
            ;;
        -w|--workflow)
            WORKFLOW="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        -v|--verbosity)
            VERBOSITY="$2"
            shift 2
            ;;
        -m|--model)
            MODEL="$2"
            shift 2
            ;;
        --build)
            BUILD_IMAGE=true
            shift
            ;;
        --interactive)
            INTERACTIVE=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Check if domain is provided
if [[ -z "$DOMAIN" ]]; then
    print_error "Domain is required!"
    show_usage
    exit 1
fi

# Check if .env file exists
if [[ ! -f ".env" ]]; then
    print_warning ".env file not found. Make sure you have Google Cloud credentials configured."
    print_info "Create a .env file with:"
    echo "GOOGLE_PROJECT_ID=your-project-id"
    echo "GOOGLE_REGION=us-central1"
fi

# Build image if requested
if [[ "$BUILD_IMAGE" == "true" ]]; then
    print_info "Building Docker image..."
    docker build -t recon-ai-agent .
    print_success "Docker image built successfully!"
fi

# Create necessary directories
mkdir -p reports cache credentials

# Check if credentials directory has service account key
if [[ ! -f "credentials/service-account.json" ]]; then
    print_warning "No service account key found in credentials/service-account.json"
    print_info "You can either:"
    print_info "1. Place your service account key in credentials/service-account.json"
    print_info "2. Use Application Default Credentials (gcloud auth application-default login)"
fi

# Prepare Docker run command
DOCKER_CMD="docker run --rm"

# Add interactive mode if requested
if [[ "$INTERACTIVE" == "true" ]]; then
    DOCKER_CMD="$DOCKER_CMD -it"
fi

# Add environment variables
DOCKER_CMD="$DOCKER_CMD --env-file .env"

# Add volumes
DOCKER_CMD="$DOCKER_CMD -v $(pwd)/reports:/app/reports"
DOCKER_CMD="$DOCKER_CMD -v $(pwd)/cache:/app/cache"

# Add credentials volume if service account file exists
if [[ -f "credentials/service-account.json" ]]; then
    DOCKER_CMD="$DOCKER_CMD -v $(pwd)/credentials:/app/credentials:ro"
fi

# Add image name
DOCKER_CMD="$DOCKER_CMD recon-ai-agent"

# Add application arguments
DOCKER_CMD="$DOCKER_CMD python main.py"
DOCKER_CMD="$DOCKER_CMD -d $DOMAIN"
DOCKER_CMD="$DOCKER_CMD -w $WORKFLOW"
DOCKER_CMD="$DOCKER_CMD -o $OUTPUT_FORMAT"
DOCKER_CMD="$DOCKER_CMD -v $VERBOSITY"
DOCKER_CMD="$DOCKER_CMD -m $MODEL"

print_info "Running Recon AI-Agent with the following configuration:"
print_info "Domain: $DOMAIN"
print_info "Workflow: $WORKFLOW"
print_info "Output Format: $OUTPUT_FORMAT"
print_info "Verbosity: $VERBOSITY"
print_info "Model: $MODEL"
echo ""

print_info "Executing: $DOCKER_CMD"
echo ""

# Run the command
eval $DOCKER_CMD

# Check exit code
if [[ $? -eq 0 ]]; then
    print_success "Recon AI-Agent completed successfully!"
    print_info "Reports can be found in the ./reports directory"
else
    print_error "Recon AI-Agent failed!"
    exit 1
fi 