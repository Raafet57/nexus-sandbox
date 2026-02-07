#!/bin/bash
# =============================================================================
# Nexus Global Payments Sandbox — Replit Startup Script
# =============================================================================
# Runs the Demo Dashboard in mock mode (no Docker/backend required).
# The frontend has a complete mock data layer that simulates the full
# Nexus payment flow including quotes, fees, and payment lifecycle.
# =============================================================================

set -e

echo "🌐 Nexus Global Payments Sandbox"
echo "================================="
echo ""

cd services/demo-dashboard

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
  echo "📦 Installing dependencies..."
  npm install
fi

echo "🚀 Starting Demo Dashboard (mock mode)..."
echo "   Dashboard: https://${REPL_SLUG}.${REPL_OWNER}.repl.co"
echo "   Local:     http://localhost:5000"
echo ""
echo "💡 Mock mode provides the full UI experience with simulated data."
echo "   For the full backend, run locally with Docker:"
echo "   docker compose -f docker-compose.lite.yml up -d"
echo ""

# Start Vite dev server
VITE_MOCK_DATA=true npx vite --host 0.0.0.0 --port 5000
