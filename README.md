# Recon AI-Agent

Recon AI-Agent is an advanced reconnaissance framework for security professionals that leverages AI capabilities to gather, analyze, and report on target web applications and networks.

## Features

- **AI-Powered Analysis**: Uses Google's Gemini AI models to interpret and analyze reconnaissance data
- **Multiple Workflow Types**: Choose from standard, quick, targeted, stealth, or comprehensive workflows
- **Extensive Tool Collection**: Includes tools for DNS analysis, WHOIS, port scanning, technology detection, HTTP header analysis, subdomain enumeration, and more
- **Web Application Security Focus**: Detect CMS, analyze SSL/TLS configurations, identify WAFs, and check for CORS misconfigurations
- **Flexible Output Formats**: Generate reports in Markdown, HTML, or JSON format

## Installation

### Prerequisites

- Python 3.9 or higher
- Google Cloud account (for Vertex AI access)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/recon-ai-agent.git
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
     ```
     GOOGLE_API_KEY=your_api_key
     GOOGLE_PROJECT_ID=your_project_id
     ```

## Available Workflows

### Standard Workflow
Balanced reconnaissance with most tools enabled. Good for general security assessment.
```bash
python main.py -d example.com -w standard
```

### Quick Workflow
Fast reconnaissance with limited scope. Good for initial discovery.
```bash
python main.py -d example.com -w quick
```

### Deep Workflow
Thorough reconnaissance with all tools enabled and maximum data collection. Takes longer to complete.
```bash
python main.py -d example.com -w deep
```

### Targeted Workflow
Focused reconnaissance on specific security aspects. Use with --target-type option.
```bash
python main.py -d example.com -w targeted --target-type ssl
```

Available target types:
- `web`: Focus on web application security issues
- `api`: Focus on API security issues
- `ssl`: Focus on SSL/TLS security issues
- `waf`: Focus on WAF detection and analysis
- `cms`: Focus on CMS detection and security

### Stealth Workflow
Stealthy reconnaissance using only passive techniques to minimize detection. Avoids active scans.
```bash
python main.py -d example.com -w stealth --delay 3.0 --jitter 1.0
```

### Comprehensive Workflow
Complete reconnaissance using all available tools with parallel execution for faster results.
```bash
python main.py -d example.com -w comprehensive --parallelism 4
```

## Usage Examples

### Basic Usage
```bash
python main.py -d example.com
```

### Output Formats
```bash
python main.py -d example.com -o markdown  # Default
python main.py -d example.com -o html
python main.py -d example.com -o json
```

### Specifying Tools
Enable or disable specific tools:
```bash
python main.py -d example.com --disable-ports --enable-subdomains
```

### Port Scanning Options
```bash
python main.py -d example.com --ports "80,443,8080-8090"
```

### Get Workflow Help
```bash
python main.py --help-workflows
```

## Available Tools

- **DNS Reconnaissance**: Analyze DNS records
- **WHOIS Lookup**: Gather domain registration information
- **HTTP Headers Analysis**: Analyze HTTP response headers
- **Subdomain Enumeration**: Discover subdomains of the target
- **Port Scanning**: Identify open ports
- **OSINT Gathering**: Use Google dorking techniques
- **Technology Detection**: Identify web technologies and frameworks
- **Website Screenshots**: Capture visual evidence
- **Endpoint Crawling**: Discover website endpoints and API paths
- **SSL/TLS Analysis**: Check certificate and configuration security
- **WAF Detection**: Identify and analyze web application firewalls
- **CORS Configuration Checks**: Identify CORS misconfigurations
- **CMS Detection**: Detect content management systems and versions

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.