# Quick Start Guide

Get up and running with Recon AI-Agent in under 5 minutes using Docker. **We've completely fixed permission issues and automated the setup!**

## 🚀 Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed
- Google Cloud account with Vertex AI API enabled
- Basic command line knowledge

## ⚡ Quick Setup

**Get started in 3 commands:**

```bash
# 1. Fix permissions and setup environment
chmod +x fix-permissions.sh docker-setup.sh
./fix-permissions.sh && ./docker-setup.sh

# 2. Edit .env with your Google Cloud Project ID
nano .env  # Edit GOOGLE_PROJECT_ID=your-actual-project-id

# 3. Run your first scan!
docker compose run --rm recon-ai-agent python main.py -d testphp.vulnweb.com
```

**That's it! No more permission errors, everything just works!** ✅

## 📋 Manual Setup (Alternative)

<details>
<summary>Click to expand manual setup instructions</summary>

### Step 1: Download and Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Winz18/recon-ai-agent
   cd recon-ai-agent
   ```

2. **Create environment file:**
   ```bash
   # Create .env file
   cat > .env << EOF
   GOOGLE_PROJECT_ID=your-google-cloud-project-id
   GOOGLE_REGION=us-central1
   TARGET_DOMAIN=google.com
   UID=1000
   GID=1000
   EOF
   ```

### Step 2: Google Cloud Authentication

Choose one of these authentication methods:

#### Option A: Service Account Key (Recommended)
```bash
# Create credentials directory
mkdir credentials

# Download your service account key from Google Cloud Console
# Save it as credentials/application_default_credentials.json
```

#### Option B: Application Default Credentials
```bash
# Install gcloud CLI and authenticate
gcloud auth application-default login
```

### Step 3: Build and Run

#### Docker Compose (Recommended):
```bash
# Build and run
docker compose up --build
```

#### Linux/macOS Scripts:
```bash
# Make script executable
chmod +x docker-run.sh

# Build and run in one command
./docker-run.sh --build -d example.com
```

#### Windows PowerShell:
```powershell
# Build and run
.\docker-run.ps1 -Domain example.com -Build
```

</details>

## 🎯 Your First Scan

Once setup is complete, try these example scans:

### 🐳 Docker Compose (Recommended)

```bash
# Basic reconnaissance
docker compose run --rm recon-ai-agent python main.py -d example.com

# Quick assessment with HTML output
docker compose run --rm recon-ai-agent python main.py -d example.com -w quick -o html

# Comprehensive analysis with high verbosity
docker compose run --rm recon-ai-agent python main.py -d example.com -w comprehensive -o html -v 2

# Start services in background
docker compose up -d

# View logs
docker compose logs -f recon-ai-agent
```

### Alternative: Using Scripts

#### Linux/macOS
```bash
# Basic scan
./docker-run.sh -d example.com

# Quick assessment
./docker-run.sh -d example.com -w quick -o html

# Comprehensive analysis
./docker-run.sh -d example.com -w comprehensive -v 2
```

#### Windows PowerShell
```powershell
# Basic scan
.\docker-run.ps1 -Domain example.com

# Quick assessment
.\docker-run.ps1 -Domain example.com -Workflow quick -OutputFormat html

# Comprehensive analysis
.\docker-run.ps1 -Domain example.com -Workflow comprehensive -Verbosity 2
```

## 📊 Viewing Results

Reports are saved in the `./reports` directory:

```bash
# List generated reports
ls -la reports/

# View HTML report (if generated)
open reports/*.html      # macOS
start reports/*.html     # Windows
xdg-open reports/*.html  # Linux

# Serve reports via web browser (Docker Compose)
docker compose run --rm -p 8000:8000 recon-ai-agent python -m http.server 8000 --directory reports
# Then open http://localhost:8000 in your browser
```

## 🔧 Common Commands

### 🏆 Docker Compose Commands (Recommended)

| Action | Command |
|--------|---------|
| **Basic scan** | `docker compose run --rm recon-ai-agent python main.py -d example.com` |
| **Quick scan** | `docker compose run --rm recon-ai-agent python main.py -d example.com -w quick` |
| **HTML output** | `docker compose run --rm recon-ai-agent python main.py -d example.com -o html` |
| **Verbose mode** | `docker compose run --rm recon-ai-agent python main.py -d example.com -v 3` |
| **Interactive shell** | `docker compose run --rm -it recon-ai-agent bash` |
| **View logs** | `docker compose logs -f recon-ai-agent` |
| **Health check** | `docker compose ps` |

### Using Scripts

| Action | Linux/macOS | Windows |
|--------|-------------|---------|
| Build image | `./docker-run.sh --build -d example.com` | `.\docker-run.ps1 -Domain example.com -Build` |
| Quick scan | `./docker-run.sh -d example.com -w quick` | `.\docker-run.ps1 -Domain example.com -Workflow quick` |
| HTML output | `./docker-run.sh -d example.com -o html` | `.\docker-run.ps1 -Domain example.com -OutputFormat html` |
| Verbose mode | `./docker-run.sh -d example.com -v 3` | `.\docker-run.ps1 -Domain example.com -Verbosity 3` |
| Interactive mode | `./docker-run.sh --interactive -d example.com` | `.\docker-run.ps1 -Domain example.com -Interactive` |

### Using Make (Linux/macOS only)

```bash
# Quick commands
make scan-quick DOMAIN=example.com
make scan-deep DOMAIN=example.com
make scan-stealth DOMAIN=example.com

# With custom output
make scan-comprehensive DOMAIN=example.com OUTPUT=html

# Targeted scans
make scan-targeted-ssl DOMAIN=example.com
make scan-targeted-web DOMAIN=example.com
```

## 🛠️ Available Workflows

| Workflow | Purpose | Time | Docker Compose Example |
|----------|---------|------|------------------------|
| `quick` | Fast initial discovery | 2-5 min | `docker compose run --rm recon-ai-agent python main.py -d example.com -w quick` |
| `standard` | Balanced assessment | 5-15 min | `docker compose run --rm recon-ai-agent python main.py -d example.com` |
| `deep` | Thorough analysis | 15-30 min | `docker compose run --rm recon-ai-agent python main.py -d example.com -w deep` |
| `comprehensive` | All tools, parallel | 10-20 min | `docker compose run --rm recon-ai-agent python main.py -d example.com -w comprehensive` |
| `stealth` | Passive techniques | 10-25 min | `docker compose run --rm recon-ai-agent python main.py -d example.com -w stealth` |
| `targeted` | Specific focus areas | 5-15 min | `docker compose run --rm recon-ai-agent python main.py -d example.com -w targeted` |

## 🎨 Output Formats

### Markdown (Default)
```bash
docker compose run --rm recon-ai-agent python main.py -d example.com -o markdown
```
- Human-readable text format
- Good for documentation
- Easy to share and version control

### HTML
```bash
docker compose run --rm recon-ai-agent python main.py -d example.com -o html
```
- Rich formatting with CSS
- Charts and graphs
- Perfect for presentations

### JSON
```bash
docker compose run --rm recon-ai-agent python main.py -d example.com -o json
```
- Machine-readable format
- API integration
- Automated processing

## 🚨 Important Notes

### Legal Considerations
⚠️ **Only scan domains you own or have explicit permission to test!**

- Corporate domains require written authorization
- Respect rate limits and terms of service
- Use stealth mode in sensitive environments

### Performance Tips
- Use `quick` workflow for initial assessment
- Run `comprehensive` workflow during off-peak hours
- Increase verbosity (`-v 2` or `-v 3`) for debugging
- Monitor resource usage with `docker compose ps`

## 🛠️ Troubleshooting (Fixed!)

### ✅ Permission Errors (Completely Fixed)

**If you see:**
```
[Errno 13] Permission denied: '/app/credentials/application_default_credentials.json'
```

**Solution:**
```bash
./fix-permissions.sh
```

This automatically fixes all permission issues!

### Common Issues & Quick Fixes

| Issue | Quick Fix | Command |
|-------|-----------|---------|
| **Permission denied** | Run permission fix | `./fix-permissions.sh` |
| **Missing .env file** | Run setup script | `./docker-setup.sh` |
| **Container won't start** | Check logs | `docker compose logs recon-ai-agent` |
| **Redis issues** | Check health | `docker compose ps` |
| **Build failures** | Clean rebuild | `docker compose build --no-cache` |

### 🔍 Debugging Commands

```bash
# Check service health
docker compose ps

# View detailed logs
docker compose logs -f recon-ai-agent

# Access container shell
docker compose run --rm -it recon-ai-agent bash

# Test configuration
docker compose config

# Clean rebuild everything
docker compose down && docker compose build --no-cache
```

## 🎯 Next Steps

1. **Start with quick scans** to test the setup
2. **Read the detailed documentation**: [DOCKER.md](../DOCKER.md) and [DOCKER_COMPOSE_FIXES.md](../DOCKER_COMPOSE_FIXES.md)
3. **Try different workflows** to understand capabilities
4. **Explore advanced options** like targeted workflows
5. **Set up CI/CD integration** for automated scanning

## 🆕 What's New

- ✅ **No more permission errors** - Completely fixed!
- ✅ **Automated setup scripts** - One-click configuration
- ✅ **Health monitoring** - Services now have health checks
- ✅ **Better resource management** - Memory and CPU limits
- ✅ **Enhanced security** - Proper user mapping and read-only mounts

**Happy scanning!** 🎉 