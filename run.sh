#!/usr/bin/env bash
# LexAudit Quick Setup & Launch Script (Bash for Linux / macOS)
# Usage: chmod +x run.sh && ./run.sh

set -e

echo ""
echo "=========================================================="
echo "                ⚖️  LexAudit Startup Script                "
echo "  Indian Law Compliance Auditor & Multilingual Grounded Q&A"
echo "=========================================================="
echo ""

# 1. Environment Setup
if [ ! -f .env ]; then
    echo "[1/3] Creating .env file from template..."
    cp .env.example .env
    echo "  -> Created .env! Update your API keys in .env if needed."
else
    echo "[1/3] Found existing .env file."
fi

# 2. Check Docker
echo "[2/3] Checking Docker installation..."
if command -v docker >/dev/null 2>&1; then
    echo "  -> Docker detected: $(docker --version)"
else
    echo "  [!] Docker is not installed or not running in PATH."
    echo "      Please install Docker Desktop and start it first."
    exit 1
fi

# 3. Build & Launch Containers
echo "[3/3] Building and starting LexAudit containers..."
echo ""

docker compose up --build -d

echo ""
echo "=========================================================="
echo "          🎉 LexAudit is Running Successfully!            "
echo "=========================================================="
echo "  Web App:       http://localhost:3000"
echo "  Backend API:   http://localhost:8000"
echo "  API Docs:      http://localhost:8000/docs"
echo "=========================================================="
echo ""
echo "To view real-time logs, run: docker compose logs -f"
echo "To stop the application, run:  docker compose down"
echo ""
