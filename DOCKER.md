# Docker Setup and Usage Guide

This guide provides comprehensive instructions for running the Recon AI-Agent using Docker.

## Quick Start

### Prerequisites

1. **Docker**: Install Docker Desktop on your system
   - Windows: Download from [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
   - macOS: Download from [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
   - Linux: Install via package manager or [Docker Engine](https://docs.docker.com/engine/install/)

2. **Google Cloud Credentials**: Set up authentication for Vertex AI
   - Option 1: Service Account Key (recommended for containers)
   - Option 2: Application Default Credentials

### Environment Setup

1. **Create Environment File**
   
   Create a `.env` file in the project root:
   ```env
   GOOGLE_PROJECT_ID=your-google-cloud-project-id
   GOOGLE_REGION=us-central1
   TARGET_DOMAIN=google.com
   ```

2. **Set Up Google Cloud Authentication**

   **Option A: Service Account Key (Recommended)**
   ```bash
   # Create credentials directory
   mkdir credentials
   
   # Download your service account key from Google Cloud Console
   # Save it as credentials/service-account.json
   ```

   **Option B: Application Default Credentials**
   ```bash
   # Install gcloud CLI and authenticate
   gcloud auth application-default login
   ```

## Building the Docker Image

### Method 1: Using Docker Command
```bash
docker build -t recon-ai-agent .
```

### Method 2: Using Docker Compose
```bash
docker-compose build
```

### Method 3: Using Convenience Scripts
```bash
# Linux/macOS
./docker-run.sh --build -d example.com

# Windows PowerShell
.\docker-run.ps1 -Domain example.com -Build
```

## Running the Application

### Method 1: Direct Docker Commands

**Basic Usage:**
```bash
docker run --rm \
  --env-file .env \
  -v $(pwd)/reports:/app/reports \
  -v $(pwd)/cache:/app/cache \
  -v $(pwd)/credentials:/app/credentials:ro \
  recon-ai-agent \
  python main.py -d example.com
```

**Advanced Usage:**
```bash
docker run --rm \
  --env-file .env \
  -v $(pwd)/reports:/app/reports \
  -v $(pwd)/cache:/app/cache \
  -v $(pwd)/credentials:/app/credentials:ro \
  recon-ai-agent \
  python main.py -d example.com -w comprehensive -o html -v 2
```

### Method 2: Using Docker Compose

**Basic Usage:**
```bash
docker-compose run --rm recon-ai-agent python main.py -d example.com
```

**Custom Workflow:**
```bash
docker-compose run --rm recon-ai-agent \
  python main.py -d example.com -w stealth -o json
```

### Method 3: Using Convenience Scripts (Recommended)

**Linux/macOS:**
```bash
# Basic scan
./docker-run.sh -d example.com

# Comprehensive scan with HTML output
./docker-run.sh -d example.com -w comprehensive -o html

# Stealth scan with high verbosity
./docker-run.sh -d example.com -w stealth -v 2

# Build and run
./docker-run.sh --build -d example.com
```

**Windows PowerShell:**
```powershell
# Basic scan
.\docker-run.ps1 -Domain example.com

# Comprehensive scan with HTML output
.\docker-run.ps1 -Domain example.com -Workflow comprehensive -OutputFormat html

# Stealth scan with high verbosity
.\docker-run.ps1 -Domain example.com -Workflow stealth -Verbosity 2

# Build and run
.\docker-run.ps1 -Domain example.com -Build
```

## Configuration Options

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GOOGLE_PROJECT_ID` | Google Cloud Project ID | Yes | - |
| `GOOGLE_REGION` | Google Cloud Region | Yes | us-central1 |
| `TARGET_DOMAIN` | Default target domain | No | google.com |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account key | No | /app/credentials/service-account.json |

### Volume Mounts

| Host Path | Container Path | Purpose | Mode |
|-----------|----------------|---------|------|
| `./reports` | `/app/reports` | Store scan reports | rw |
| `./cache` | `/app/cache` | Cache reconnaissance data | rw |
| `./credentials` | `/app/credentials` | Google Cloud credentials | ro |

### Available Workflows

| Workflow | Description | Use Case |
|----------|-------------|----------|
| `standard` | Balanced reconnaissance with most tools | General security assessment |
| `quick` | Fast reconnaissance with limited scope | Initial discovery |
| `deep` | Thorough reconnaissance with all tools | Complete security audit |
| `targeted` | Focused on specific security aspects | Specialized testing |
| `stealth` | Passive techniques to minimize detection | Covert reconnaissance |
| `comprehensive` | All tools with parallel execution | Fast complete assessment |

### Output Formats

- `markdown` - Markdown format (default)
- `html` - HTML report with styling
- `json` - JSON format for programmatic use

## Examples

### 1. Quick Domain Assessment
```bash
# Linux/macOS
./docker-run.sh -d target.com -w quick -o html

# Windows
.\docker-run.ps1 -Domain target.com -Workflow quick -OutputFormat html
```

### 2. Comprehensive Security Audit
```bash
# Linux/macOS
./docker-run.sh -d target.com -w comprehensive -v 2

# Windows
.\docker-run.ps1 -Domain target.com -Workflow comprehensive -Verbosity 2
```

### 3. Stealth Reconnaissance
```bash
# Linux/macOS
./docker-run.sh -d target.com -w stealth -o json

# Windows
.\docker-run.ps1 -Domain target.com -Workflow stealth -OutputFormat json
```

### 4. SSL/TLS Focused Assessment
```bash
# Linux/macOS
./docker-run.sh -d target.com -w targeted --target-type ssl

# Windows - Use docker-compose for advanced options
docker-compose run --rm recon-ai-agent \
  python main.py -d target.com -w targeted --target-type ssl
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```
   Error: Could not automatically determine credentials
   ```
   **Solution:** Ensure your `.env` file contains correct `GOOGLE_PROJECT_ID` and either set up service account key or use `gcloud auth application-default login`.

2. **Permission Errors**
   ```
   Permission denied: '/app/reports'
   ```
   **Solution:** Check that the host directories have proper permissions. The container runs as a non-root user.

3. **Docker Build Failures**
   ```
   Error building image
   ```
   **Solution:** Ensure Docker has enough resources allocated and your internet connection is stable for downloading dependencies.

4. **Playwright Browser Issues**
   ```
   Browser not found
   ```
   **Solution:** The Dockerfile installs Chromium automatically. If issues persist, rebuild the image.

### Performance Optimization

1. **Resource Allocation**
   - Adjust Docker Desktop memory allocation (minimum 2GB recommended)
   - Use `--parallelism` option for comprehensive workflow

2. **Caching**
   - The application uses disk caching for reconnaissance data
   - Cache is persistent across container runs via volume mounts

3. **Network Configuration**
   - Ensure Docker has internet access for external API calls
   - Some corporate firewalls may block certain reconnaissance activities

### Debugging

**Interactive Mode:**
```bash
# Linux/macOS
./docker-run.sh --interactive -d example.com

# Windows
.\docker-run.ps1 -Domain example.com -Interactive
```

**Shell Access:**
```bash
docker run --rm -it \
  --env-file .env \
  -v $(pwd)/reports:/app/reports \
  -v $(pwd)/cache:/app/cache \
  recon-ai-agent \
  /bin/bash
```

**View Logs:**
```bash
# Add verbose output
./docker-run.sh -d example.com -v 3

# Or use Docker logs
docker logs <container-id>
```

## Security Considerations

1. **Credentials Security**
   - Never commit `.env` files or service account keys to version control
   - Use the provided `.dockerignore` to exclude sensitive files
   - Mount credentials as read-only volumes

2. **Network Security**
   - The container runs as a non-root user for security
   - No unnecessary ports are exposed
   - Use the `no-new-privileges` security option

3. **Legal and Ethical Use**
   - Only scan domains you own or have explicit permission to test
   - Respect rate limits and terms of service
   - Use stealth workflow for sensitive environments

## Advanced Configuration

### Custom Docker Compose Setup

Create a custom `docker-compose.override.yml`:
```yaml
version: '3.8'

services:
  recon-ai-agent:
    environment:
      - CUSTOM_VAR=value
    volumes:
      - ./custom-config:/app/custom-config
    networks:
      - custom-network
    
networks:
  custom-network:
    external: true
```

### Multi-Stage Build for Production

For production environments, consider creating a multi-stage Dockerfile:
```dockerfile
FROM python:3.12-slim as builder
# Build dependencies...

FROM python:3.12-slim as runtime
# Copy only necessary files from builder
```

### Integration with CI/CD

Example GitHub Actions workflow:
```yaml
name: Security Scan
on: [push]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Recon Scan
        run: |
          docker build -t recon-ai-agent .
          docker run --rm \
            -e GOOGLE_PROJECT_ID=${{ secrets.GOOGLE_PROJECT_ID }} \
            -e GOOGLE_REGION=us-central1 \
            -v $(pwd)/reports:/app/reports \
            recon-ai-agent \
            python main.py -d ${{ github.event.repository.name }}.com
```

This comprehensive Docker setup provides a secure, portable, and easy-to-use environment for running the Recon AI-Agent across different platforms and use cases. 