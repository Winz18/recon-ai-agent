# Docker Setup and Usage Guide

This guide provides comprehensive instructions for running the Recon AI-Agent using Docker. **We've completely fixed permission issues and added automated setup scripts!**

## 🚀 Quick Start (Fixed & Automated!)

### Prerequisites

1. **Docker**: Install Docker Desktop on your system
   - Windows: Download from [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
   - macOS: Download from [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
   - Linux: Install via package manager or [Docker Engine](https://docs.docker.com/engine/install/)

2. **Google Cloud Credentials**: Set up authentication for Vertex AI
   - Option 1: Service Account Key (recommended for containers)
   - Option 2: Application Default Credentials

### 🎯 Automated Setup (Recommended)

**One-command setup that fixes everything:**

```bash
# 1. Fix permissions (eliminates "Permission denied" errors)
chmod +x fix-permissions.sh && ./fix-permissions.sh

# 2. Setup environment and validate configuration
chmod +x docker-setup.sh && ./docker-setup.sh

# 3. Edit .env with your Google Cloud Project ID
nano .env

# 4. Run your first scan!
docker compose run --rm recon-ai-agent python main.py -d testphp.vulnweb.com
```

### Manual Environment Setup (Alternative)

<details>
<summary>Click to expand manual setup instructions</summary>

1. **Create Environment File**
   
   Create a `.env` file in the project root:
   ```env
   GOOGLE_PROJECT_ID=your-google-cloud-project-id
   GOOGLE_REGION=us-central1
   TARGET_DOMAIN=google.com
   UID=1000
   GID=1000
   ```

2. **Set Up Google Cloud Authentication**

   **Option A: Service Account Key (Recommended)**
   ```bash
   # Create credentials directory
   mkdir credentials
   
   # Download your service account key from Google Cloud Console
   # Save it as credentials/application_default_credentials.json
   ```

   **Option B: Application Default Credentials**
   ```bash
   # Install gcloud CLI and authenticate
   gcloud auth application-default login
   ```

</details>

## Building the Docker Image

### Method 1: Using Docker Compose (Recommended)
```bash
# Build and run in one command
docker compose up --build

# Or build only
docker compose build
```

### Method 2: Using Docker Command
```bash
docker build -t recon-ai-agent .
```

### Method 3: Using Convenience Scripts
```bash
# Linux/macOS
./docker-run.sh --build -d example.com

# Windows PowerShell
.\docker-run.ps1 -Domain example.com -Build
```

## Running the Application

### 🥇 Method 1: Docker Compose (Recommended - Fixed!)

**The docker-compose setup is now completely fixed with proper permissions:**

**Basic Usage:**
```bash
# Most common usage - basic scan
docker compose run --rm recon-ai-agent python main.py -d example.com

# Comprehensive scan with HTML output
docker compose run --rm recon-ai-agent python main.py -d example.com -w comprehensive -o html

# Start services in background
docker compose up -d

# View logs
docker compose logs -f recon-ai-agent
```

**Advanced Usage:**
```bash
# Stealth reconnaissance
docker compose run --rm recon-ai-agent python main.py -d example.com -w stealth -v 2

# Targeted SSL analysis
docker compose run --rm recon-ai-agent python main.py -d example.com -w targeted --target-type ssl

# Multiple parallel scans
docker compose exec recon-ai-agent python main.py -d example1.com &
docker compose exec recon-ai-agent python main.py -d example2.com &
```

### Method 2: Direct Docker Commands

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

### Method 3: Using Convenience Scripts

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

| Variable | Description | Required | Default | Set by Script |
|----------|-------------|----------|---------|---------------|
| `GOOGLE_PROJECT_ID` | Google Cloud Project ID | Yes | - | `docker-setup.sh` |
| `GOOGLE_REGION` | Google Cloud Region | Yes | us-central1 | `docker-setup.sh` |
| `TARGET_DOMAIN` | Default target domain | No | google.com | `docker-setup.sh` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account key | No | /app/credentials/application_default_credentials.json | `docker-setup.sh` |
| `UID` | User ID for Docker mapping | No | 1000 | `fix-permissions.sh` |
| `GID` | Group ID for Docker mapping | No | 1000 | `fix-permissions.sh` |

### Volume Mounts

| Host Path | Container Path | Purpose | Mode | Fixed |
|-----------|----------------|---------|------|-------|
| `./reports` | `/app/reports` | Store scan reports | rw | ✅ |
| `./cache` | `/app/cache` | Cache reconnaissance data | rw | ✅ |
| `./credentials` | `/app/credentials` | Google Cloud credentials | ro | ✅ |
| `./gcloud` | `/app/gcloud` | Alternative ADC path | ro | ✅ |

### Available Workflows

| Workflow | Description | Use Case | Docker Compose Example |
|----------|-------------|----------|------------------------|
| `standard` | Balanced reconnaissance with most tools | General security assessment | `docker compose run --rm recon-ai-agent python main.py -d example.com` |
| `quick` | Fast reconnaissance with limited scope | Initial discovery | `docker compose run --rm recon-ai-agent python main.py -d example.com -w quick` |
| `deep` | Thorough reconnaissance with all tools | Complete security audit | `docker compose run --rm recon-ai-agent python main.py -d example.com -w deep` |
| `targeted` | Focused on specific security aspects | Specialized testing | `docker compose run --rm recon-ai-agent python main.py -d example.com -w targeted` |
| `stealth` | Passive techniques to minimize detection | Covert reconnaissance | `docker compose run --rm recon-ai-agent python main.py -d example.com -w stealth` |
| `comprehensive` | All tools with parallel execution | Fast complete assessment | `docker compose run --rm recon-ai-agent python main.py -d example.com -w comprehensive` |

### Output Formats

- `markdown` - Markdown format (default)
- `html` - HTML report with styling
- `json` - JSON format for programmatic use

## Examples

### 1. Quick Domain Assessment
```bash
# Docker Compose (recommended)
docker compose run --rm recon-ai-agent python main.py -d target.com -w quick -o html

# Alternative scripts
./docker-run.sh -d target.com -w quick -o html              # Linux/macOS
.\docker-run.ps1 -Domain target.com -Workflow quick -OutputFormat html  # Windows
```

### 2. Comprehensive Security Audit
```bash
# Docker Compose (recommended)
docker compose run --rm recon-ai-agent python main.py -d target.com -w comprehensive -v 2

# Alternative scripts
./docker-run.sh -d target.com -w comprehensive -v 2         # Linux/macOS
.\docker-run.ps1 -Domain target.com -Workflow comprehensive -Verbosity 2  # Windows
```

### 3. Stealth Reconnaissance
```bash
# Docker Compose (recommended)
docker compose run --rm recon-ai-agent python main.py -d target.com -w stealth -o json

# Alternative scripts
./docker-run.sh -d target.com -w stealth -o json            # Linux/macOS
.\docker-run.ps1 -Domain target.com -Workflow stealth -OutputFormat json  # Windows
```

### 4. SSL/TLS Focused Assessment
```bash
# Docker Compose (recommended)
docker compose run --rm recon-ai-agent python main.py -d target.com -w targeted --target-type ssl

# Alternative scripts
./docker-run.sh -d target.com -w targeted --target-type ssl # Linux/macOS
```

### 5. Multiple Domain Scanning
```bash
# Sequential scanning
for domain in example1.com example2.com example3.com; do
  docker compose run --rm recon-ai-agent python main.py -d $domain -w quick -o json
done

# Parallel scanning (background services)
docker compose up -d
docker compose exec recon-ai-agent python main.py -d example1.com &
docker compose exec recon-ai-agent python main.py -d example2.com &
docker compose exec recon-ai-agent python main.py -d example3.com &
```

## 🔧 Troubleshooting (Completely Fixed!)

### ✅ Fixed: Permission Denied Errors

**Previous Issue:**
```
[Errno 13] Permission denied: '/app/credentials/application_default_credentials.json'
```

**✅ Solution (Automated):**
```bash
./fix-permissions.sh
```

This script automatically:
- Fixes file permissions on all directories
- Sets proper UID/GID mapping in .env file
- Ensures container can access mounted volumes
- Works for any user (including root)

### Common Issues & Solutions

| Issue | Automated Solution | Manual Solution |
|-------|-------------------|-----------------|
| **Permission denied errors** | `./fix-permissions.sh` | Set proper file permissions |
| **Missing .env file** | `./docker-setup.sh` | Copy from env.sample |
| **Invalid Google Cloud credentials** | Check setup guide | Verify project ID and credentials |
| **Container won't start** | `docker compose logs recon-ai-agent` | Check configuration |
| **Redis connection issues** | Health checks enabled | `docker compose ps` |

### Health Monitoring (New!)

Both services now have health checks:

```bash
# Check service health
docker compose ps

# View health check logs
docker compose logs redis
docker compose logs recon-ai-agent
```

### Performance Optimization

1. **Resource Allocation**
   - Docker Compose now has proper memory limits (2GB max)
   - CPU limits configured (1 CPU max)
   - Redis memory limited to 256MB with LRU eviction

2. **Caching**
   - Enhanced Redis configuration with persistence
   - Disk caching for reconnaissance data
   - Cache survives container restarts

3. **Network Configuration**
   - Proper Docker network setup
   - Health checks for service dependencies

### Debugging

**Interactive Mode:**
```bash
# Docker Compose
docker compose run --rm -it recon-ai-agent bash

# Scripts
./docker-run.sh --interactive -d example.com              # Linux/macOS
.\docker-run.ps1 -Domain example.com -Interactive        # Windows
```

**View Logs:**
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f recon-ai-agent
docker compose logs -f redis

# With timestamps
docker compose logs -f -t recon-ai-agent
```

**Development Shell:**
```bash
# Start services and access shell
docker compose up -d
docker compose exec recon-ai-agent bash

# Direct shell access
docker compose run --rm -it recon-ai-agent bash
```

## Security Considerations

### ✅ Enhanced Security Features

1. **User Mapping**
   - Container runs as current user (not root)
   - Proper UID/GID mapping prevents permission issues
   - No privilege escalation with `no-new-privileges:true`

2. **Credentials Security**
   - Read-only mounts for credential directories
   - Never commit `.env` files to version control
   - Support for both service account keys and ADC

3. **Network Security**
   - Isolated Docker network
   - No unnecessary port exposure
   - Health checks for service monitoring

4. **Legal and Ethical Use**
   - Only scan domains you own or have explicit permission to test
   - Respect rate limits and terms of service
   - Use stealth workflow for sensitive environments

## Advanced Configuration

### Custom Docker Compose Setup

Create a `docker-compose.override.yml`:
```yaml
services:
  recon-ai-agent:
    environment:
      - CUSTOM_TIMEOUT=30
    volumes:
      - ./custom-reports:/app/custom-reports
    ports:
      - "8080:8080"  # If you add a web interface
    
  # Add custom services
  custom-redis:
    image: redis:7-alpine
    command: redis-server --port 6380
```

### Health Check Configuration

Customize health checks in docker-compose.yml:
```yaml
services:
  recon-ai-agent:
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
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
      - name: Setup and Run Scan
        env:
          GOOGLE_PROJECT_ID: ${{ secrets.GOOGLE_PROJECT_ID }}
          GOOGLE_REGION: us-central1
        run: |
          ./fix-permissions.sh
          ./docker-setup.sh
          docker compose run --rm recon-ai-agent \
            python main.py -d ${{ github.event.repository.name }}.com -o json
      - name: Upload Reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: reports/
```

## 🎯 Best Practices

1. **Always run permission fix first:** `./fix-permissions.sh`
2. **Use Docker Compose for consistency:** Better than direct docker commands
3. **Monitor health checks:** `docker compose ps` to verify service status
4. **Use .env files:** Keep credentials secure and organized
5. **Regular updates:** Pull latest images and rebuild periodically

This comprehensive Docker setup now provides a **completely fixed**, secure, portable, and easy-to-use environment for running the Recon AI-Agent across different platforms and use cases. 