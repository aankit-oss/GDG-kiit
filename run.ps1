# LexAudit Quick Setup & Launch Script (PowerShell for Windows)
# Usage: .\run.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "                ⚖️  LexAudit Startup Script                " -ForegroundColor Cyan
Write-Host "  Indian Law Compliance Auditor & Multilingual Grounded Q&A" -ForegroundColor Subtitle
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Environment Setup
if (-not (Test-Path ".env")) {
    Write-Host "[1/3] Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "  -> Created .env! Update your API keys in .env if needed." -ForegroundColor Green
} else {
    Write-Host "[1/3] Found existing .env file." -ForegroundColor Green
}

# 2. Check Docker
Write-Host "[2/3] Checking Docker installation..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "  -> Docker detected: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "  [!] Docker is not installed or not running in PATH." -ForegroundColor Red
    Write-Host "      Please install Docker Desktop and start it first." -ForegroundColor Red
    Exit 1
}

# 3. Build & Launch Containers
Write-Host "[3/3] Building and starting LexAudit containers..." -ForegroundColor Yellow
Write-Host ""

docker compose up --build -d

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "          🎉 LexAudit is Running Successfully!            " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Web App:       http://localhost:3000" -ForegroundColor White
Write-Host "  Backend API:   http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs:      http://localhost:8000/docs" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To view real-time logs, run: docker compose logs -f" -ForegroundColor Gray
Write-Host "To stop the application, run:  docker compose down" -ForegroundColor Gray
Write-Host ""
