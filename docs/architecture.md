# Recon AI-Agent Architecture

This document provides a comprehensive overview of the Recon AI-Agent architecture, an advanced reconnaissance framework for security professionals that leverages AutoGen Framework and Google Vertex AI to automate the process of footprinting and reconnaissance in security testing.

## Architecture Overview

```
                                  +------------------+
                                  |                  |
                                  |   Docker Layer   |
                                  |  (Containerized) |
                                  |                  |
                                  +--------+---------+
                                           |
                                           |
                                           v
                                  +------------------+
                                  |                  |
                                  |   Main CLI App   |
                                  |                  |
                                  +--------+---------+
                                           |
                                           |
                                           v
+----------------+            +------------+------------+             +----------------+
|                |            |                         |             |                |
|  Configuration +----------->+   Workflow Controller   +------------>+    Reporter    |
|                |            |                         |             |                |
+----------------+            +------------+------------+             +----------------+
                                           |
                                           |
                                           v
                              +------------+------------+
                              |                         |
                              |   AI Agent Orchestrator |
                              |                         |
                              +------------+------------+
                                           |
                    +--------------------+ | +----------------------+
                    |                    | | |                      |
                    v                    v v v                      v
            +-------+------+    +--------+----------+    +---------+----------+
            |              |    |                   |    |                    |
            | Domain Intel |    | Network Recon     |    | OSINT Gathering    |
            | Agent        |    | Agent             |    | Agent              |
            |              |    |                   |    |                    |
            +-------+------+    +--------+----------+    +---------+----------+
                    |                    |                          |
                    |                    |                          |
                    v                    v                          v
            +-------+------+    +--------+----------+    +---------+----------+
            |              |    |                   |    |                    |
            | DNS Tools    |    | Port Scanner      |    | Google Dorking     |
            | WHOIS Tools  |    | Header Analysis   |    | Tech Detection     |
            |              |    |                   |    | Screenshot         |
            +--------------+    +-------------------+    +--------------------+
```

## Docker Architecture

### Container Structure

```
Docker Host
├── recon-ai-agent:latest (Image)
│   ├── Base: python:3.12-slim
│   ├── System Tools: curl, wget, nmap, openssl
│   ├── Python Dependencies: AG2, Vertex AI, etc.
│   ├── Playwright Browsers: Chromium
│   └── Application Code
│
├── Volumes
│   ├── ./reports -> /app/reports (Scan results)
│   ├── ./cache -> /app/cache (Cached data)
│   └── ./credentials -> /app/credentials (GCP credentials)
│
└── Network: recon-network (Isolated)
```

### Multi-Platform Support

```
┌─── Linux ────┐    ┌─── Windows ───┐    ┌─── macOS ────┐
│              │    │               │    │              │
│ docker-run.sh│    │docker-run.ps1 │    │docker-run.sh │
│              │    │               │    │              │
│ Makefile     │    │ PowerShell    │    │ Makefile     │
│              │    │ Native        │    │              │
└──────────────┘    └───────────────┘    └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                ┌───────────▼──────────┐
                │                      │
                │  Docker Engine       │
                │  (Cross-platform)    │
                │                      │
                └──────────────────────┘
```

## Core Components

### 1. Container Layer

**Docker Components:**
- **Dockerfile**: Defines container environment with all dependencies
- **docker-compose.yml**: Orchestration for multi-container deployment
- **Scripts**: docker-run.sh (Linux/macOS), docker-run.ps1 (Windows)
- **Makefile**: Automation tools for development and deployment

**Benefits:**
- **Isolation**: Complete separation from host system
- **Consistency**: Same environment across all platforms
- **Portability**: Easy deployment on any system
- **Security**: Container runs with non-root user

### 2. Main CLI Application

**File:** `main.py`

The primary entry point of the application, providing a command-line interface for users to:
- Configure reconnaissance parameters
- Select workflow to execute
- Run individual tools
- View and save reports

**Docker Integration:**
- Supports environment variables from container
- Integrates with volume mounts for persistent storage
- Health checks for container monitoring

### 3. Configuration Module

**Directory:** `config/`

Manages all application settings:
- Connection configuration for Vertex AI and AutoGen
- Default settings for tools
- Environment variable management from container
- Configuration file reading from `.env` files and Docker secrets

**Docker Features:**
- Environment variable injection
- Secret management via Docker secrets
- Configuration file mounting

### 4. AI Agents (AutoGen Framework)

**Directory:** `agents/`

Implements intelligent agents orchestrated by the AutoGen Framework:

- **ReconPlanner Agent:** Plans reconnaissance strategy based on user input
- **DomainIntel Agent:** Specializes in domain-related intelligence gathering
- **NetworkRecon Agent:** Performs network scanning and analysis tasks
- **WebAppRecon Agent:** Analyzes web applications and technologies
- **OSINTGathering Agent:** Collects open-source intelligence
- **Reporter Agent:** Aggregates data and generates reports

**Container Benefits:**
- Isolated execution environment
- Consistent AI model access
- Resource management and limits

### 5. Tools Module

**Directory:** `tools/`

Collection of reconnaissance tools used by agents:

- **network.py:** DNS lookup, WHOIS lookup tools
- **web.py:** HTTP header analysis, security information
- **port_scanner.py:** Port scanning capabilities
- **search.py:** Subdomain discovery
- **google_dorking.py:** Google dorks execution
- **tech_detector.py:** Web technology detection
- **screenshot.py:** Website screenshot capture (with Playwright in container)
- **tool_decorator.py:** Decorator for marking and tracking tool usage

**Docker Enhancements:**
- Pre-installed system tools (nmap, openssl, curl)
- Playwright browsers available in container
- Network isolation for security scanning

### 6. Workflows Module

**Directory:** `workflows/`

Defines standard reconnaissance processes:

- **standard_recon_workflow.py:** Complete process including all steps
- **quick_workflow.py:** Fast process for initial assessment
- **deep_workflow.py:** Detailed process with all tools
- **stealth_workflow.py:** Covert process with passive techniques
- **comprehensive_workflow.py:** Parallel execution for performance
- **targeted_workflow.py:** Focus on specific security aspects

**Container Optimization:**
- Parallel processing support
- Resource-aware execution
- Timeout management

### 7. Reports & Storage

**Persistent Volumes:**
- **./reports:** Store reports in Markdown, HTML, JSON formats
- **./cache:** Cache reconnaissance data for reuse
- **./credentials:** Mount point for Google Cloud credentials

**Container Features:**
- Persistent storage across container restarts
- Backup and restore capabilities
- Log aggregation

## Deployment Architectures

### 1. Single Container Deployment

```
Host System
└── Docker Container (recon-ai-agent)
    ├── Application Code
    ├── Python Runtime
    ├── System Tools
    └── Mounted Volumes
        ├── /app/reports (Host: ./reports)
        ├── /app/cache (Host: ./cache)
        └── /app/credentials (Host: ./credentials)
```

### 2. Docker Compose Deployment

```
Docker Compose Stack
├── recon-ai-agent (Main application)
│   ├── Environment variables
│   ├── Volume mounts
│   └── Network: recon-network
│
├── redis (Optional caching)
│   ├── Persistent data
│   └── Network: recon-network
│
└── Volumes
    ├── recon_reports
    ├── recon_cache
    └── redis_data
```

### 3. Production Cluster Deployment

```
Container Orchestration (K8s/Swarm)
├── Load Balancer
├── Multiple recon-ai-agent instances
├── Shared storage (NFS/EBS)
├── Centralized logging
├── Monitoring & metrics
└── Auto-scaling based on workload
```

## Workflow Execution with Docker

1. **Container Startup**
   - Docker engine initializes container from image
   - Mount volumes for persistent storage
   - Load environment variables and secrets
   - Initialize health checks

2. **Application Initialization**
   - Main CLI app starts in container
   - Configuration module loads settings from container environment
   - AI agents connect to Vertex AI

3. **Workflow Execution**
   - User selects workflow through CLI or scripts
   - Container executes reconnaissance tasks
   - Tools use pre-installed system utilities
   - Results saved to mounted volumes

4. **Report Generation**
   - Data aggregation in container
   - Report generation (Markdown/HTML/JSON)
   - Output saved to persistent volumes
   - Container cleanup (if --rm flag)

## Security Architecture

### Container Security

```
Security Layers
├── Host Security
│   ├── Docker daemon security
│   ├── User namespace isolation
│   └── Seccomp profiles
│
├── Container Security
│   ├── Non-root user execution (appuser:1000)
│   ├── Read-only root filesystem
│   ├── No new privileges
│   └── Resource limits (CPU/Memory)
│
├── Network Security
│   ├── Isolated Docker networks
│   ├── Firewall rules
│   └── Encrypted communication (TLS)
│
└── Data Security
    ├── Encrypted credentials storage
    ├── Secure volume mounts
    └── Audit logging
```

### Authentication Flow

```
Container -> Google Cloud
├── Service Account Key (mounted volume)
├── Application Default Credentials
├── Vertex AI API authentication
└── Encrypted API communication
```

## Performance & Scalability

### Resource Management

```
Container Resources
├── CPU Limits: 1-2 cores (configurable)
├── Memory Limits: 2GB default (configurable)
├── Storage: Persistent volumes
└── Network: Isolated networks
```

### Scaling Strategies

1. **Horizontal Scaling**: Multiple container instances
2. **Vertical Scaling**: Increase container resources  
3. **Parallel Processing**: Multiple workflows simultaneously
4. **Caching**: Persistent data caching across runs

## Monitoring & Observability

### Container Metrics

```
Monitoring Stack
├── Container Stats (CPU, Memory, Network)
├── Application Logs (structured JSON)
├── Health Checks (endpoint monitoring)
├── Performance Metrics (scan duration, success rates)
└── Error Tracking (failed scans, API errors)
```

### Logging Architecture

```
Log Flow
Container Logs -> Docker Logging Driver -> Log Aggregation -> Analysis
├── Application logs (/app/logs)
├── System logs (container events)
├── Audit logs (scan activities)
└── Error logs (failures, exceptions)
```

## Extensibility with Docker

### Adding New Tools

1. **Update Dockerfile** to install system dependencies
2. **Add Python packages** to requirements.txt
3. **Rebuild container image**
4. **Test in isolated environment**

### Custom Workflows

1. **Create workflow file** in workflows/
2. **Test in development container**
3. **Deploy via volume mount** or image rebuild
4. **Update documentation**

## Backup & Recovery

### Data Protection

```
Backup Strategy
├── Volume Backups (automated)
│   ├── Reports archive
│   ├── Cache snapshots
│   └── Configuration backups
│
├── Image Backups
│   ├── Tagged releases
│   ├── Version control
│   └── Registry storage
│
└── Disaster Recovery
    ├── Container recreation
    ├── Data restoration
    └── Service continuity
```

## Migration & Updates

### Zero-Downtime Updates

```
Update Process
├── Pull new image
├── Test in staging environment
├── Rolling update deployment
├── Health check validation
└── Rollback capability
```

## Technology Stack

### Core Technologies
- **Python 3.12**: Core runtime environment
- **AutoGen Framework**: AI agent orchestration
- **Google Vertex AI**: AI model integration
- **Playwright**: Browser automation and screenshots
- **Docker**: Containerization platform

### Security Tools
- **nmap**: Network port scanning
- **openssl**: SSL/TLS analysis
- **curl/wget**: HTTP analysis
- **DNS utilities**: Domain intelligence

### Development Tools
- **pytest**: Testing framework
- **black/flake8**: Code formatting and linting
- **pre-commit**: Git hooks for quality control

## Limitations and Challenges

### Container-Specific Challenges

- **Resource Overhead**: Container has overhead compared to native execution
- **Network Complexity**: Container networking can be complex in enterprise environments
- **Storage Performance**: Volume mounts may be slower than native filesystem
- **Security Scanning**: Need to scan container images for vulnerabilities

### Mitigations

- **Performance Tuning**: Optimize container resources and caching
- **Network Optimization**: Use host networking when necessary
- **Storage Solutions**: High-performance storage backends
- **Security Practices**: Regular image updates and vulnerability scanning

## Future Enhancements

### Planned Features
- **Kubernetes Helm Charts**: For production orchestration
- **Multi-architecture Images**: ARM64 support for Apple Silicon
- **Plugin System**: External tool integration
- **Web UI**: Browser-based interface
- **API Server**: REST API for integration

### Scalability Improvements
- **Distributed Processing**: Multi-node execution
- **Queue System**: Job queue management
- **Load Balancing**: Intelligent workload distribution
- **Auto-scaling**: Dynamic resource allocation

This Docker-enhanced architecture provides a solid foundation for deployment, scaling, and maintenance of Recon AI-Agent in production environments with focus on security, performance, and operational excellence.