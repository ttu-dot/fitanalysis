#!/bin/bash
# FIT Running Data Analyzer - Development Startup Script (macOS/Linux)

# Set UTF-8 encoding
export LANG=en_US.UTF-8

# Print header
echo "======================================"
echo "FIT Running Data Analyzer"
echo "Development Environment"
echo "======================================"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "Python version:"
python3 --version
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "[1/3] Creating virtual environment..."
    python3 -m venv .venv
    echo "      ✓ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "[2/3] Activating virtual environment..."
source .venv/bin/activate
echo "      ✓ Virtual environment activated"
echo ""

# Install/update dependencies
echo "[3/3] Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r backend/requirements.txt
echo "      ✓ Dependencies installed"
echo ""

# Start server
echo "======================================"
echo "Starting server..."
echo "Access at: http://127.0.0.1:8082"
echo "Press Ctrl+C to stop server"
echo "======================================"
echo ""

cd backend
python main.py
