# docker-run.ps1 - PowerShell script to run Recon AI-Agent with Docker

param(
    [Parameter(Mandatory=$true)]
    [string]$Domain,
    
    [string]$Workflow = "standard",
    [string]$OutputFormat = "markdown",
    [int]$Verbosity = 1,
    [string]$Model = "gemini-2.5-pro-preview-05-06",
    [switch]$Build,
    [switch]$Interactive,
    [switch]$Help
)

# Colors for output
$script:Red = "`e[31m"
$script:Green = "`e[32m"
$script:Yellow = "`e[33m"
$script:Blue = "`e[34m"
$script:Reset = "`e[0m"

function Write-Info {
    param([string]$Message)
    Write-Host "${script:Blue}[INFO]${script:Reset} $Message"
}

function Write-Success {
    param([string]$Message)
    Write-Host "${script:Green}[SUCCESS]${script:Reset} $Message"
}

function Write-Warning {
    param([string]$Message)
    Write-Host "${script:Yellow}[WARNING]${script:Reset} $Message"
}

function Write-Error {
    param([string]$Message)
    Write-Host "${script:Red}[ERROR]${script:Reset} $Message"
}

function Show-Usage {
    Write-Host "Usage: .\docker-run.ps1 -Domain <domain> [OPTIONS]"
    Write-Host ""
    Write-Host "Parameters:"
    Write-Host "  -Domain <string>          Target domain to scan (required)"
    Write-Host "  -Workflow <string>        Workflow type (default: standard)"
    Write-Host "                           Options: standard, quick, deep, targeted, stealth, comprehensive"
    Write-Host "  -OutputFormat <string>    Output format (default: markdown)"
    Write-Host "                           Options: markdown, html, json"
    Write-Host "  -Verbosity <int>          Verbosity level 0-3 (default: 1)"
    Write-Host "  -Model <string>           AI model to use (default: gemini-2.5-pro-preview-05-06)"
    Write-Host "  -Build                    Build Docker image before running"
    Write-Host "  -Interactive              Run in interactive mode"
    Write-Host "  -Help                     Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\docker-run.ps1 -Domain example.com"
    Write-Host "  .\docker-run.ps1 -Domain example.com -Workflow comprehensive -OutputFormat html"
    Write-Host "  .\docker-run.ps1 -Domain example.com -Workflow stealth -Verbosity 2"
    Write-Host "  .\docker-run.ps1 -Domain example.com -Build"
}

# Show help if requested
if ($Help) {
    Show-Usage
    exit 0
}

# Validate workflow parameter
$ValidWorkflows = @("standard", "quick", "deep", "targeted", "stealth", "comprehensive")
if ($Workflow -notin $ValidWorkflows) {
    Write-Error "Invalid workflow: $Workflow"
    Write-Host "Valid workflows: $($ValidWorkflows -join ', ')"
    exit 1
}

# Validate output format parameter
$ValidFormats = @("markdown", "html", "json")
if ($OutputFormat -notin $ValidFormats) {
    Write-Error "Invalid output format: $OutputFormat"
    Write-Host "Valid formats: $($ValidFormats -join ', ')"
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Warning ".env file not found. Make sure you have Google Cloud credentials configured."
    Write-Info "Create a .env file with:"
    Write-Host "GOOGLE_PROJECT_ID=your-project-id"
    Write-Host "GOOGLE_REGION=us-central1"
}

# Build image if requested
if ($Build) {
    Write-Info "Building Docker image..."
    docker build -t recon-ai-agent .
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Docker image built successfully!"
    } else {
        Write-Error "Failed to build Docker image!"
        exit 1
    }
}

# Create necessary directories
$directories = @("reports", "cache", "credentials")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Info "Created directory: $dir"
    }
}

# Check if credentials directory has service account key
if (-not (Test-Path "credentials\service-account.json")) {
    Write-Warning "No service account key found in credentials\service-account.json"
    Write-Info "You can either:"
    Write-Info "1. Place your service account key in credentials\service-account.json"
    Write-Info "2. Use Application Default Credentials (gcloud auth application-default login)"
}

# Prepare Docker run command
$DockerArgs = @("run", "--rm")

# Add interactive mode if requested
if ($Interactive) {
    $DockerArgs += "-it"
}

# Add environment variables
if (Test-Path ".env") {
    $DockerArgs += "--env-file", ".env"
}

# Add volumes
$CurrentPath = (Get-Location).Path
$DockerArgs += "-v", "${CurrentPath}\reports:/app/reports"
$DockerArgs += "-v", "${CurrentPath}\cache:/app/cache"

# Add credentials volume if service account file exists
if (Test-Path "credentials\service-account.json") {
    $DockerArgs += "-v", "${CurrentPath}\credentials:/app/credentials:ro"
}

# Add image name
$DockerArgs += "recon-ai-agent"

# Add application arguments
$DockerArgs += "python", "main.py"
$DockerArgs += "-d", $Domain
$DockerArgs += "-w", $Workflow
$DockerArgs += "-o", $OutputFormat
$DockerArgs += "-v", $Verbosity.ToString()
$DockerArgs += "-m", $Model

Write-Info "Running Recon AI-Agent with the following configuration:"
Write-Info "Domain: $Domain"
Write-Info "Workflow: $Workflow"
Write-Info "Output Format: $OutputFormat"
Write-Info "Verbosity: $Verbosity"
Write-Info "Model: $Model"
Write-Host ""

Write-Info "Executing: docker $($DockerArgs -join ' ')"
Write-Host ""

# Run the command
& docker @DockerArgs

# Check exit code
if ($LASTEXITCODE -eq 0) {
    Write-Success "Recon AI-Agent completed successfully!"
    Write-Info "Reports can be found in the .\reports directory"
} else {
    Write-Error "Recon AI-Agent failed!"
    exit 1
} 