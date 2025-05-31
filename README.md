# Recon AI-Agent

Recon AI-Agent is an advanced reconnaissance framework for security professionals that leverages AI capabilities to gather, analyze, and report on target web applications and networks.

## 🚀 Features

- **AI-Powered Analysis**: Uses Google's Gemini AI models to interpret and analyze reconnaissance data
- **Multiple Workflow Types**: Choose from standard, quick, targeted, stealth, or comprehensive workflows
- **Extensive Tool Collection**: Includes tools for DNS analysis, WHOIS, port scanning, technology detection, HTTP header analysis, subdomain enumeration, and more
- **Web Application Security Focus**: Detect CMS, analyze SSL/TLS configurations, identify WAFs, and check for CORS misconfigurations
- **Flexible Output Formats**: Generate reports in Markdown, HTML, or JSON format
- **🐳 Docker Support**: Fully containerized with cross-platform support
- **📊 Multiple Deployment Options**: Run via Docker, Docker Compose, or traditional Python setup

## 📦 Quick Start with Docker (Recommended)

The easiest way to get started is using Docker. No need to install Python dependencies or worry about system compatibility.

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed on your system
- Google Cloud account with Vertex AI API enabled

### 1. Setup Environment

Create a `.env` file in the project root:
```env
GOOGLE_PROJECT_ID=your-google-cloud-project-id
GOOGLE_REGION=us-central1
TARGET_DOMAIN=google.com
```

### 2. Set Up Google Cloud Authentication

**Option A: Service Account Key (Recommended for containers)**
```bash
# Create credentials directory
mkdir credentials

# Download your service account key from Google Cloud Console
# Save it as credentials/service-account.json
```

**Option B: Application Default Credentials**
```bash
gcloud auth application-default login
```

### 3. Build and Run

**Linux/macOS:**
```bash
# Quick start - build and run
./docker-run.sh --build -d example.com

# Or just run if image exists
./docker-run.sh -d example.com -w comprehensive -o html
```

**Windows PowerShell:**
```powershell
# Quick start - build and run
.\docker-run.ps1 -Domain example.com -Build

# Or just run if image exists
.\docker-run.ps1 -Domain example.com -Workflow comprehensive -OutputFormat html
```

**Using Make (Linux/macOS):**
```bash
# Build image
make build

# Run quick scan
make scan-quick DOMAIN=example.com

# Run comprehensive scan with HTML output
make scan-comprehensive DOMAIN=example.com OUTPUT=html
```

**Using Docker Compose:**
```bash
# Build and run
docker-compose run --rm recon-ai-agent python main.py -d example.com
```

## 🔧 Installation Options

### Option 1: Docker (Recommended)

See the [Quick Start](#-quick-start-with-docker-recommended) section above.

For detailed Docker setup and usage instructions, see **[DOCKER.md](DOCKER.md)**.

### Option 2: Traditional Python Setup

<details>
<summary>Click to expand Python installation instructions</summary>

#### Prerequisites
- Python 3.9 or higher
- Google Cloud account (for Vertex AI access)

#### Setup Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/Winz18/recon-ai-agent
   cd recon-ai-agent
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up your Google Cloud credentials:
   - Create a `.env` file in the project root
   - Add your Google Cloud credentials:
     ```env
     GOOGLE_PROJECT_ID=your_project_id
     GOOGLE_REGION=us-central1
     ```

5. Run the application:
   ```bash
   python main.py -d example.com
   ```

</details>

## 🎯 Available Workflows

| Workflow | Description | Use Case | Docker Example |
|----------|-------------|----------|----------------|
| **standard** | Balanced reconnaissance with most tools | General security assessment | `./docker-run.sh -d example.com` |
| **quick** | Fast reconnaissance with limited scope | Initial discovery | `./docker-run.sh -d example.com -w quick` |
| **deep** | Thorough reconnaissance with all tools | Complete security audit | `./docker-run.sh -d example.com -w deep` |
| **targeted** | Focused on specific security aspects | Specialized testing | `./docker-run.sh -d example.com -w targeted` |
| **stealth** | Passive techniques to minimize detection | Covert reconnaissance | `./docker-run.sh -d example.com -w stealth` |
| **comprehensive** | All tools with parallel execution | Fast complete assessment | `./docker-run.sh -d example.com -w comprehensive` |

### Targeted Workflow Options

When using the `targeted` workflow, specify a target type:

- `web`: Focus on web application security issues
- `api`: Focus on API security issues
- `ssl`: Focus on SSL/TLS security issues
- `waf`: Focus on WAF detection and analysis
- `cms`: Focus on CMS detection and security

**Example:**
```bash
./docker-run.sh -d example.com -w targeted --target-type ssl
```

## 📊 Usage Examples

### Docker Examples (Recommended)

```bash
# Basic reconnaissance
./docker-run.sh -d example.com

# Comprehensive scan with HTML output
./docker-run.sh -d example.com -w comprehensive -o html -v 2

# Stealth reconnaissance with high verbosity
./docker-run.sh -d example.com -w stealth -v 3

# Targeted SSL/TLS analysis
make scan-targeted-ssl DOMAIN=example.com

# Quick scan for multiple domains
for domain in example1.com example2.com; do
  ./docker-run.sh -d $domain -w quick -o json
done
```

### Traditional Python Examples

```bash
# Basic usage
python main.py -d example.com

# Output formats
python main.py -d example.com -o markdown  # Default
python main.py -d example.com -o html
python main.py -d example.com -o json

# Tool-specific options
python main.py -d example.com --disable-ports --enable-subdomains
python main.py -d example.com --ports "80,443,8080-8090"

# Get help
python main.py --help-workflows
```

## 🛠️ Available Tools

- **DNS Reconnaissance**: Analyze DNS records and discover subdomains
- **WHOIS Lookup**: Gather domain registration information and ownership details
- **HTTP Headers Analysis**: Analyze security headers and server information
- **Subdomain Enumeration**: Discover subdomains using multiple techniques
- **Port Scanning**: Identify open ports and running services
- **OSINT Gathering**: Use Google dorking and search engine intelligence
- **Technology Detection**: Identify web technologies, frameworks, and CMS
- **Website Screenshots**: Capture visual evidence of web interfaces
- **Endpoint Crawling**: Discover website endpoints and API paths
- **SSL/TLS Analysis**: Check certificate validity and security configuration
- **WAF Detection**: Identify and analyze web application firewalls
- **CORS Configuration Checks**: Identify CORS misconfigurations and security issues
- **CMS Detection**: Detect content management systems and versions

## 📁 Output and Reports

Reports are automatically saved in the `./reports` directory:

```
reports/
├── example.com_20241201_140530.md    # Markdown report
├── example.com_20241201_140530.html  # HTML report (if requested)
├── example.com_20241201_140530.json  # JSON data (if requested)
└── raw_data/
    └── example.com_20241201_140530/  # Raw reconnaissance data
```

### Viewing Reports

```bash
# List generated reports
make show-reports

# View latest HTML report (if available)
open reports/*.html  # macOS
start reports/*.html # Windows
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GOOGLE_PROJECT_ID` | Google Cloud Project ID | Yes | - |
| `GOOGLE_REGION` | Google Cloud Region | No | us-central1 |
| `TARGET_DOMAIN` | Default target domain | No | google.com |

### Tool Configuration

Most tools can be enabled/disabled via command line:

```bash
# Disable specific tools
python main.py -d example.com --disable-ports --disable-screenshot

# Enable specific tools only
python main.py -d example.com --enable-dns --enable-whois --disable-all-others

# Configure port scanning
python main.py -d example.com --ports "22,80,443,8080-8090" --port-timeout 5
```

## 🧪 Development and Testing

### Using Docker for Development

```bash
# Build development image
make dev-build

# Start development shell
make dev-shell

# Run tests in container
make test
```

### Running Tests

```bash
# Docker
docker run --rm recon-ai-agent python -m pytest tests/ -v

# Traditional
python -m pytest tests/ -v
```

## 📚 Documentation

- **[DOCKER.md](DOCKER.md)** - Comprehensive Docker setup and usage guide
- **[docs/architecture.md](docs/architecture.md)** - System architecture and design
- **[docs/adding_tools.md](docs/adding_tools.md)** - Guide for adding new reconnaissance tools
- **[docs/defining_workflows.md](docs/defining_workflows.md)** - Creating custom workflows

## 🚨 Security and Legal Considerations

⚠️ **Important**: This tool is designed for authorized security testing only.

- Only scan domains you own or have explicit written permission to test
- Respect rate limits and terms of service of external APIs
- Use the `stealth` workflow in sensitive environments
- Be aware that some reconnaissance activities may be logged by target systems
- Follow responsible disclosure practices for any vulnerabilities discovered

## 🤝 Contributing

Contributions are welcome! Please see our contribution guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Adding New Tools

See **[docs/adding_tools.md](docs/adding_tools.md)** for detailed instructions on adding new reconnaissance tools.

### Creating Workflows

See **[docs/defining_workflows.md](docs/defining_workflows.md)** for information on creating custom workflows.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Cloud Vertex AI for AI capabilities
- The AutoGen Framework for agent orchestration
- The security research community for tool inspiration
- All contributors who have helped improve this project

---

**⭐ If you find this tool useful, please consider giving it a star on GitHub!**
