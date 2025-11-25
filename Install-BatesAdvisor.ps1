# =============================================================================
# Bates Technical College Student Advisor Agent
# Windows Server 2025 - Automated Installation Script
# =============================================================================
# 
# USAGE:
#   1. Run PowerShell as Administrator
#   2. Set execution policy: Set-ExecutionPolicy Bypass -Scope Process -Force
#   3. Run: .\Install-BatesAdvisor.ps1
#
# =============================================================================

param(
    [string]$GoogleApiKey = "",
    [string]$InstallPath = "C:\Projects\student-advisor-capstone-adk",
    [switch]$SkipDockerInstall,
    [switch]$SkipReboot
)

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Bates Technical College Student Advisor Agent" -ForegroundColor Cyan
Write-Host " Windows Server 2025 Installation Script" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# -----------------------------------------------------------------------------
# Check Prerequisites
# -----------------------------------------------------------------------------
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Administrator)) {
    Write-Host "[ERROR] This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "        Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Running as Administrator" -ForegroundColor Green

# -----------------------------------------------------------------------------
# Step 1: Install Containers Feature
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[STEP 1/6] Checking Windows Containers feature..." -ForegroundColor Yellow

$containersFeature = Get-WindowsFeature -Name Containers
if ($containersFeature.Installed) {
    Write-Host "[OK] Containers feature already installed" -ForegroundColor Green
} else {
    Write-Host "[INFO] Installing Containers feature..." -ForegroundColor Cyan
    Install-WindowsFeature -Name Containers
    Write-Host "[OK] Containers feature installed" -ForegroundColor Green
    $needsReboot = $true
}

# -----------------------------------------------------------------------------
# Step 2: Install Docker
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[STEP 2/6] Checking Docker installation..." -ForegroundColor Yellow

if (-not $SkipDockerInstall) {
    $dockerInstalled = Get-Command docker -ErrorAction SilentlyContinue
    
    if ($dockerInstalled) {
        Write-Host "[OK] Docker already installed: $(docker --version)" -ForegroundColor Green
    } else {
        Write-Host "[INFO] Installing Docker..." -ForegroundColor Cyan
        
        # Install NuGet provider
        Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force | Out-Null
        
        # Install Docker provider
        Install-Module -Name DockerMsftProvider -Repository PSGallery -Force
        
        # Install Docker
        Install-Package -Name docker -ProviderName DockerMsftProvider -Force
        
        Write-Host "[OK] Docker installed successfully" -ForegroundColor Green
        $needsReboot = $true
    }
}

# -----------------------------------------------------------------------------
# Step 3: Configure Docker Service
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[STEP 3/6] Configuring Docker service..." -ForegroundColor Yellow

$dockerService = Get-Service -Name Docker -ErrorAction SilentlyContinue
if ($dockerService) {
    Set-Service -Name Docker -StartupType Automatic
    if ($dockerService.Status -ne "Running") {
        Start-Service Docker
    }
    Write-Host "[OK] Docker service configured and running" -ForegroundColor Green
} else {
    Write-Host "[WARN] Docker service not found - may need reboot" -ForegroundColor Yellow
}

# -----------------------------------------------------------------------------
# Step 4: Clone Repository
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[STEP 4/6] Setting up application..." -ForegroundColor Yellow

# Check if Git is installed
$gitInstalled = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitInstalled) {
    Write-Host "[INFO] Installing Git..." -ForegroundColor Cyan
    
    # Download Git installer
    $gitUrl = "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe"
    $gitInstaller = "$env:TEMP\GitInstaller.exe"
    Invoke-WebRequest -Uri $gitUrl -OutFile $gitInstaller
    
    # Silent install
    Start-Process -FilePath $gitInstaller -ArgumentList "/VERYSILENT /NORESTART" -Wait
    
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    
    Write-Host "[OK] Git installed" -ForegroundColor Green
}

# Create install directory
$parentPath = Split-Path -Parent $InstallPath
if (-not (Test-Path $parentPath)) {
    New-Item -ItemType Directory -Path $parentPath -Force | Out-Null
}

# Clone or update repository
if (Test-Path $InstallPath) {
    Write-Host "[INFO] Updating existing installation..." -ForegroundColor Cyan
    Push-Location $InstallPath
    git pull origin development
    Pop-Location
} else {
    Write-Host "[INFO] Cloning repository..." -ForegroundColor Cyan
    git clone https://github.com/GCB-89/student-advisor-capstone-adk.git $InstallPath
}

Write-Host "[OK] Application files ready at: $InstallPath" -ForegroundColor Green

# -----------------------------------------------------------------------------
# Step 5: Configure Environment
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[STEP 5/6] Configuring environment..." -ForegroundColor Yellow

if ([string]::IsNullOrEmpty($GoogleApiKey)) {
    Write-Host ""
    Write-Host "[INPUT REQUIRED]" -ForegroundColor Magenta
    $GoogleApiKey = Read-Host "Enter your Google API Key"
}

if (-not [string]::IsNullOrEmpty($GoogleApiKey)) {
    # Set environment variable permanently
    [System.Environment]::SetEnvironmentVariable("GOOGLE_API_KEY", $GoogleApiKey, "Machine")
    $env:GOOGLE_API_KEY = $GoogleApiKey
    Write-Host "[OK] Google API Key configured" -ForegroundColor Green
} else {
    Write-Host "[WARN] No API key provided - you'll need to set GOOGLE_API_KEY manually" -ForegroundColor Yellow
}

# -----------------------------------------------------------------------------
# Step 6: Configure Firewall
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[STEP 6/6] Configuring firewall..." -ForegroundColor Yellow

$firewallRule = Get-NetFirewallRule -DisplayName "Bates Advisor Agent" -ErrorAction SilentlyContinue
if ($firewallRule) {
    Write-Host "[OK] Firewall rule already exists" -ForegroundColor Green
} else {
    New-NetFirewallRule -DisplayName "Bates Advisor Agent" `
        -Direction Inbound `
        -Protocol TCP `
        -LocalPort 8000 `
        -Action Allow | Out-Null
    Write-Host "[OK] Firewall rule created for port 8000" -ForegroundColor Green
}

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Installation Complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host " Application Location: $InstallPath" -ForegroundColor White
Write-Host ""
Write-Host " Next Steps:" -ForegroundColor Yellow

if ($needsReboot) {
    Write-Host "   1. REBOOT the server to complete Docker installation" -ForegroundColor Red
    Write-Host "   2. After reboot, run these commands:" -ForegroundColor White
} else {
    Write-Host "   Run these commands to start the application:" -ForegroundColor White
}

Write-Host ""
Write-Host "   cd $InstallPath" -ForegroundColor Cyan
Write-Host "   docker-compose build" -ForegroundColor Cyan
Write-Host "   docker-compose up -d" -ForegroundColor Cyan
Write-Host ""
Write-Host " Access the application at: http://localhost:8000" -ForegroundColor Green
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan

# Offer to reboot if needed
if ($needsReboot -and -not $SkipReboot) {
    Write-Host ""
    $rebootNow = Read-Host "Reboot now? (y/n)"
    if ($rebootNow -eq "y" -or $rebootNow -eq "Y") {
        Write-Host "Rebooting in 10 seconds..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        Restart-Computer -Force
    }
}
