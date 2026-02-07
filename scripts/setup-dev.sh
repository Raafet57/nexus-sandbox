#!/bin/bash
# Developer setup script for Nexus Global Payments Sandbox
# This script installs pre-commit hooks and other development tools

set -e

echo "================================"
echo "Nexus Sandbox - Developer Setup"
echo "================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not found."
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is required but not found."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo "✓ Node.js found: $(node --version)"
echo ""

# Install Python pre-commit
echo "Installing Python pre-commit..."
pip install pre-commit --quiet

# Install pre-commit hooks
echo "Setting up pre-commit hooks..."
pre-commit install

# Install npm packages for dashboard
echo ""
echo "Installing dashboard dependencies..."
cd services/demo-dashboard
npm install
cd ../..

echo ""
echo "================================"
echo "✓ Setup complete!"
echo "================================"
echo ""
echo "Pre-commit hooks are now installed."
echo "They will run automatically when you commit."
echo ""
echo "To run them manually:"
echo "  pre-commit run --all-files"
echo ""
echo "To skip hooks (not recommended):"
echo "  git commit --no-verify -m \"message\""
echo ""
