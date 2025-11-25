# 🐳 Docker Deployment Guide - Windows Server 2025

## Bates Technical College Student Advisor Agent

Complete installation and deployment guide for Windows Server 2025 environments.
## Installation Options

Choose one of the following methods:

### Option A: Automated Installation (Recommended for Quick Setup)
Run the automated PowerShell script:
```powershell
# Download and run the installer
.\Install-BatesAdvisor.ps1
```

This script automatically handles Docker installation, repository cloning, 
firewall configuration, and environment setup.

### Option B: Manual Installation (Recommended for Learning/Troubleshooting)
Follow the detailed step-by-step guide below if you want to understand 
each component or need to customize the installation.

---

## Prerequisites

- Windows Server 2025 (Desktop Experience or Core)
- Administrator access
- Internet connectivity
- Minimum 4GB RAM, 2 CPU cores, 20GB storage

---

## Part 1: Install Docker on Windows Server 2025

### Step 1: Enable Containers Feature

Open **PowerShell as Administrator** and run:

```powershell
# Install the Containers feature
Install-WindowsFeature -Name Containers -Restart
```

The server will restart automatically.

### Step 2: Install Docker Engine

After restart, open **PowerShell as Administrator**:

```powershell
# Install Docker provider
Install-Module -Name DockerMsftProvider -Repository PSGallery -Force

# Install Docker
Install-Package -Name docker -ProviderName DockerMsftProvider -Force

# Start Docker service
Start-Service Docker

# Set Docker to start automatically
Set-Service -Name Docker -StartupType Automatic

# Verify installation
docker --version
docker info
```

### Step 3: Enable Linux Containers (Required for this project)

```powershell
# Install WSL2
wsl --install

# Restart the server
Restart-Computer

# After restart, set WSL2 as default
wsl --set-default-version 2
```

### Step 4: Install Docker Desktop (Alternative Method)

If you prefer Docker Desktop:

```powershell
# Download Docker Desktop installer
Invoke-WebRequest -Uri "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe" -OutFile "$env:TEMP\DockerDesktopInstaller.exe"

# Run installer (requires GUI)
Start-Process -FilePath "$env:TEMP\DockerDesktopInstaller.exe" -Wait

# After installation, ensure Linux containers mode is enabled
# Right-click Docker icon in system tray > Switch to Linux containers
```

---

## Part 2: Deploy Bates Advisor Agent

### Step 1: Clone the Repository

```powershell
# Navigate to your preferred directory
cd C:\Projects

# Clone the repository
git clone https://github.com/GCB-89/student-advisor-capstone-adk.git
cd student-advisor-capstone-adk
```

### Step 2: Configure Environment

```powershell
# Set your Google API key as environment variable
$env:GOOGLE_API_KEY = "your_api_key_here"

# To make it permanent (survives restarts):
[System.Environment]::SetEnvironmentVariable("GOOGLE_API_KEY", "your_api_key_here", "Machine")
```

### Step 3: Build and Run with Docker Compose

```powershell
# Build the container
docker-compose build

# Start the application
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Step 4: Access the Application

Open a browser and navigate to:
```
http://localhost:8000
```

Or from another machine on the network:
```
http://YOUR_SERVER_IP:8000
```

---

## Part 3: Windows Firewall Configuration

```powershell
# Allow inbound traffic on port 8000
New-NetFirewallRule -DisplayName "Bates Advisor Agent" `
    -Direction Inbound `
    -Protocol TCP `
    -LocalPort 8000 `
    -Action Allow
```

---

## Part 4: Configure as Windows Service (Auto-Start)

### Create Scheduled Task for Auto-Start

```powershell
# Create a scheduled task to start Docker Compose on boot
$Action = New-ScheduledTaskAction -Execute "docker-compose" `
    -Argument "up -d" `
    -WorkingDirectory "C:\Projects\student-advisor-capstone-adk"

$Trigger = New-ScheduledTaskTrigger -AtStartup

$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

Register-ScheduledTask -TaskName "BatesAdvisorStartup" `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -User "SYSTEM" `
    -RunLevel Highest
```

---

## Part 5: Management Commands

### Daily Operations

```powershell
# Start the application
docker-compose up -d

# Stop the application
docker-compose down

# Restart the application
docker-compose restart

# View real-time logs
docker-compose logs -f

# Check container health
docker ps

# View resource usage
docker stats
```

### Maintenance

```powershell
# Update to latest version
git pull origin main
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Clean up old images
docker image prune -f

# View disk usage
docker system df

# Full cleanup (removes all unused data)
docker system prune -a
```

---

## Part 6: Troubleshooting

### Docker Service Issues

```powershell
# Check Docker service status
Get-Service Docker

# Restart Docker service
Restart-Service Docker

# View Docker logs
Get-EventLog -LogName Application -Source Docker -Newest 50
```

### Container Issues

```powershell
# View container logs
docker logs bates-student-advisor

# Enter container for debugging
docker exec -it bates-student-advisor /bin/bash

# Check environment variables
docker exec bates-student-advisor env | Select-String "GOOGLE"

# Restart container
docker-compose restart
```

### Network Issues

```powershell
# Check if port 8000 is listening
Get-NetTCPConnection -LocalPort 8000

# Check firewall rules
Get-NetFirewallRule -DisplayName "*Bates*"

# Test connectivity
Test-NetConnection -ComputerName localhost -Port 8000
```

### Common Errors

| Error | Solution |
|-------|----------|
| "Cannot connect to Docker daemon" | Run `Start-Service Docker` |
| "Port 8000 already in use" | Run `docker-compose down` or change port in docker-compose.yml |
| "API key not set" | Set `$env:GOOGLE_API_KEY` before running |
| "Image build failed" | Check internet connectivity, run `docker-compose build --no-cache` |

---

## Part 7: Security Considerations

### Production Hardening

```powershell
# Use Docker secrets instead of environment variables
# Create a secret file (do not commit to git!)
"your_api_key_here" | Out-File -FilePath ".\secrets\google_api_key.txt" -NoNewline

# Update docker-compose.yml to use secrets (see docker-compose.prod.yml)
```

### SSL/TLS Configuration (Production)

For production deployments, place a reverse proxy (IIS, nginx) in front:

```powershell
# Install IIS with reverse proxy capability
Install-WindowsFeature -Name Web-Server, Web-WebSockets -IncludeManagementTools

# Install URL Rewrite and ARR modules from:
# https://www.iis.net/downloads/microsoft/url-rewrite
# https://www.iis.net/downloads/microsoft/application-request-routing
```

---

## Part 8: Monitoring and Logging

### Enable Container Logging

```powershell
# View logs directory on host
Get-ChildItem -Path ".\logs"

# Follow logs in real-time
Get-Content -Path ".\logs\bates_agent.log" -Wait
```

### Windows Event Logging

```powershell
# Create custom event log source
New-EventLog -LogName Application -Source "BatesAdvisor"

# Log application events
Write-EventLog -LogName Application -Source "BatesAdvisor" -EventId 1000 -EntryType Information -Message "Bates Advisor started"
```

---

## Quick Reference Card

| Task | Command |
|------|---------|
| Start | `docker-compose up -d` |
| Stop | `docker-compose down` |
| Logs | `docker-compose logs -f` |
| Restart | `docker-compose restart` |
| Rebuild | `docker-compose build --no-cache` |
| Status | `docker ps` |
| Shell | `docker exec -it bates-student-advisor /bin/bash` |

---

## Support

- **GitHub Issues**: [student-advisor-capstone-adk](https://github.com/GCB-89/student-advisor-capstone-adk/issues)
- **Docker Docs**: [docs.docker.com](https://docs.docker.com)
- **Windows Server Docs**: [docs.microsoft.com](https://docs.microsoft.com/en-us/windows-server/)

---

*Last Updated: November 2025*
