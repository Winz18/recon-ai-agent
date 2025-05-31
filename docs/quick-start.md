# Quick Start Guide

Get up and running with Recon AI-Agent in under 5 minutes using Docker.

## 🚀 Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed
- Google Cloud account with Vertex AI API enabled
- Basic command line knowledge

## 📋 Step-by-Step Setup

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
   EOF
   ```

### Step 2: Google Cloud Authentication

Choose one of these authentication methods:

#### Option A: Service Account Key (Recommended)
```bash
# Create credentials directory
mkdir credentials

# Download your service account key from Google Cloud Console
# Save it as credentials/service-account.json
```

#### Option B: Application Default Credentials
```bash
# Install gcloud CLI and authenticate
gcloud auth application-default login
```

### Step 3: Build and Run

#### Linux/macOS:
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

#### Alternative: Using Make (Linux/macOS)
```bash
# Build image
make build

# Run scan
make scan-quick DOMAIN=example.com
```

## 🎯 Your First Scan

Once setup is complete, try these example scans:

### Basic Reconnaissance
```bash
# Linux/macOS
./docker-run.sh -d example.com

# Windows
.\docker-run.ps1 -Domain example.com
```

### Quick Assessment
```bash
# Linux/macOS
./docker-run.sh -d example.com -w quick -o html

# Windows
.\docker-run.ps1 -Domain example.com -Workflow quick -OutputFormat html
```

### Comprehensive Analysis
```bash
# Linux/macOS
./docker-run.sh -d example.com -w comprehensive -v 2

# Windows
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
```

## 🔧 Common Commands

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

| Workflow | Purpose | Time | Example |
|----------|---------|------|---------|
| `quick` | Fast initial discovery | 2-5 min | `./docker-run.sh -d example.com -w quick` |
| `standard` | Balanced assessment | 5-15 min | `./docker-run.sh -d example.com` |
| `deep` | Thorough analysis | 15-30 min | `./docker-run.sh -d example.com -w deep` |
| `comprehensive` | All tools, parallel | 10-20 min | `./docker-run.sh -d example.com -w comprehensive` |
| `stealth` | Passive techniques | 10-25 min | `./docker-run.sh -d example.com -w stealth` |
| `targeted` | Specific focus areas | 5-15 min | `./docker-run.sh -d example.com -w targeted` |

## 🎨 Output Formats

### Markdown (Default)
```bash
./docker-run.sh -d example.com -o markdown
```
- Human-readable text format
- Good for documentation
- Easy to share and version control

### HTML
```bash
./docker-run.sh -d example.com -o html
```
- Rich formatting with CSS
- Charts and graphs
- Perfect for presentations

### JSON
```bash
./docker-run.sh -d example.com -o json
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

### Troubleshooting Quick Fixes

#### Container won't start:
```bash
# Check Docker is running
docker --version

# Rebuild image
./docker-run.sh --build -d example.com
```

#### Permission denied:
```bash
# Linux/macOS: Fix permissions
chmod +x docker-run.sh

# Windows: Run PowerShell as Administrator
```

#### Authentication errors:
```bash
# Verify .env file exists and has correct values
cat .env

# Check Google Cloud credentials
gcloud auth list
```

## 🔗 Next Steps

Once you're comfortable with basic scans:

1. **Explore Advanced Features:**
   - Read [DOCKER.md](../DOCKER.md) for detailed Docker usage
   - Check [architecture.md](architecture.md) to understand the system
   - Learn about [adding new tools](adding_tools.md)

2. **Customize Workflows:**
   - Create custom workflows with [defining_workflows.md](defining_workflows.md)
   - Configure tool-specific options
   - Set up automated scanning schedules

3. **Production Deployment:**
   - Review [docker-deployment.md](docker-deployment.md) for production setup
   - Implement monitoring and logging
   - Set up backup strategies

## 💡 Pro Tips

### Batch Scanning
```bash
# Scan multiple domains
domains=("example1.com" "example2.com" "example3.com")
for domain in "${domains[@]}"; do
    ./docker-run.sh -d $domain -w quick -o json
done
```

### Custom Configuration
```bash
# Create custom environment for specific projects
cp .env .env.project1
# Edit .env.project1 with project-specific settings

# Use custom environment
docker run --rm --env-file .env.project1 -v $(pwd)/reports:/app/reports recon-ai-agent python main.py -d target.com
```

### Development Mode
```bash
# Interactive shell for debugging
make shell

# Development with hot reloading
make dev-shell
```

## 📞 Getting Help

- **Documentation:** Check the `docs/` folder for detailed guides
- **Issues:** Report bugs or request features on GitHub
- **Community:** Join discussions and share tips

---

**Ready to start? Run your first scan now:**

```bash
# Linux/macOS
./docker-run.sh --build -d google.com -w quick

# Windows
.\docker-run.ps1 -Domain google.com -Build -Workflow quick
``` 