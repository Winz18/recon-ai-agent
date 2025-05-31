# Docker Compose Fixes

## Issues Fixed

### 1. **Removed Deprecated Version Specification**
- **Issue**: Docker Compose was showing warnings about the deprecated `version` field
- **Fix**: Removed `version: '3.8'` as it's no longer needed in modern Docker Compose

### 2. **Added Environment File Support**
- **Issue**: Environment variables were only specified inline
- **Fix**: Added `env_file: - .env` to load environment variables from a file
- **Benefit**: Easier configuration management and better security

### 3. **Improved Volume Mappings**
- **Issue**: Original volume mapping for credentials was confusing (`./gcloud:/app/credentials:ro`)
- **Fix**: 
  - Separated credentials and gcloud directories
  - Added proper credentials directory mapping: `./credentials:/app/credentials:ro`
  - Added gcloud directory mapping: `./gcloud:/app/gcloud:ro`
  - Commented out Docker socket mounting as it's a security risk unless needed

### 4. **Added Health Checks**
- **Issue**: No health monitoring for containers
- **Fix**: Added health checks for both main application and Redis
- **Benefit**: Better container monitoring and restart policies

### 5. **Enhanced Redis Configuration**
- **Issue**: Basic Redis configuration without memory limits
- **Fix**: Added memory limits and eviction policy: `--maxmemory 256mb --maxmemory-policy allkeys-lru`
- **Benefit**: Prevents Redis from consuming all available memory

### 6. **Added Service Dependencies**
- **Issue**: No explicit dependency management
- **Fix**: Added `depends_on: - redis` to ensure Redis starts before the main application
- **Benefit**: Proper startup order

### 7. **Added Python Environment Variables**
- **Issue**: Missing important Python environment variables
- **Fix**: Added `PYTHONUNBUFFERED=1` and `PYTHONDONTWRITEBYTECODE=1`
- **Benefit**: Better Python runtime behavior in containers

### 8. **Fixed Docker Permissions Issues** ⭐ NEW
- **Issue**: Permission denied errors when accessing mounted credential files
- **Fix**: 
  - Added user mapping: `user: "${UID:-1000}:${GID:-1000}"`
  - Added `HOME=/tmp` environment variable
  - Created `fix-permissions.sh` script to automatically set permissions
- **Benefit**: Eliminates permission errors with mounted volumes

## Additional Files Created

### 1. **env.sample**
- Template for environment variables
- Shows required and optional configuration options
- Helps users understand what credentials are needed
- Now includes UID/GID mapping for Docker user permissions

### 2. **docker-setup.sh**
- Automated setup script for Docker Compose environment
- Creates necessary directories
- Validates configuration
- Provides helpful setup guidance
- Usage: `chmod +x docker-setup.sh && ./docker-setup.sh`

### 3. **fix-permissions.sh** ⭐ NEW
- Fixes file and directory permissions for Docker
- Automatically detects current user UID/GID
- Updates .env file with proper user mapping
- Ensures credentials files are readable by container
- Usage: `chmod +x fix-permissions.sh && ./fix-permissions.sh`

## Usage Instructions

### Quick Start (Fixed Permission Issues)
1. Run the permission fix script: `./fix-permissions.sh`
2. Run the setup script: `./docker-setup.sh`
3. Edit `.env` file with your Google Cloud Project ID
4. Ensure Google Cloud authentication is configured
5. Start the application: `docker compose up --build`

### Manual Setup
1. Copy `env.sample` to `.env`
2. Edit `.env` with your configuration
3. Run: `./fix-permissions.sh` to fix permission issues
4. Create directories: `mkdir -p reports cache credentials gcloud`
5. Configure Google Cloud authentication
6. Run: `docker compose up --build`

### Alternative: Use Existing Scripts
- For simple runs: `./docker-run.sh -d example.com`
- For PowerShell: `.\docker-run.ps1 -Domain example.com`

### If You Get Permission Errors
If you see errors like:
```
[Errno 13] Permission denied: '/app/credentials/application_default_credentials.json'
```

**Solution**: Run the permission fix script:
```bash
chmod +x fix-permissions.sh
./fix-permissions.sh
```

This will:
- Fix file permissions on credentials and directories
- Set proper UID/GID mapping in .env file
- Ensure container can access mounted volumes

## Security Improvements

1. **Docker Socket**: Commented out by default to reduce attack surface
2. **Read-only Credentials**: Credentials directories mounted as read-only
3. **No-new-privileges**: Security option added to prevent privilege escalation
4. **User Mapping**: Container runs as current user, not root
5. **Proper File Permissions**: Credentials files have appropriate read permissions

## Health Monitoring

Both services now have health checks:
- **Main Application**: Simple Python import test
- **Redis**: Redis CLI ping test

## Resource Management

- **Memory Limits**: 2GB max, 512MB reserved for main application
- **CPU Limits**: 1 CPU max, 0.5 CPU reserved for main application  
- **Redis Memory**: Limited to 256MB with LRU eviction policy

## Troubleshooting

### Common Issues and Solutions

1. **Permission Denied Errors**
   - **Solution**: Run `./fix-permissions.sh`
   - **Cause**: File permissions or UID/GID mismatch

2. **Container Won't Start**
   - **Solution**: Check `docker compose logs recon-ai-agent`
   - **Common Cause**: Missing .env file or invalid credentials

3. **Redis Connection Issues**
   - **Solution**: Ensure Redis container is running: `docker compose ps`
   - **Alternative**: Check Redis logs: `docker compose logs redis`

4. **Google Cloud Authentication Errors**
   - **Solution**: Run `gcloud auth application-default login`
   - **Alternative**: Place service account key in `credentials/application_default_credentials.json` 