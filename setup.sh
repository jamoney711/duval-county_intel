#!/bin/bash
# Quick start script for local development

echo "================================================"
echo "Duval County Lead Scraper - Quick Start"
echo "================================================"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version || { echo "❌ Python 3 not found"; exit 1; }
echo ""

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r scraper/requirements.txt

# Install Playwright browsers
echo "Installing Playwright browsers..."
python -m playwright install chromium --with-deps

# Create data directory if it doesn't exist
mkdir -p data

echo ""
echo "================================================"
echo "✅ Setup Complete!"
echo "================================================"
echo ""
echo "To run the scraper:"
echo "  source venv/bin/activate"
echo "  python scraper/fetch.py"
echo ""
echo "Results will be saved to:"
echo "  - dashboard/records.json"
echo "  - data/records.json"
echo "  - data/ghl_export.csv"
echo ""
echo "To view dashboard:"
echo "  Open dashboard/index.html in your browser"
echo ""
