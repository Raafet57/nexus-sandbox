#!/bin/bash
# =============================================================================
# Nexus Global Payments Sandbox — Replit Full-Stack Startup
# =============================================================================
# Starts the complete stack on Replit (no Docker needed):
#   1. PostgreSQL 16 (via Nix)
#   2. Redis (via Nix)
#   3. Nexus Gateway (Python/FastAPI on port 8000)
#   4. Demo Dashboard (React/Vite on port 3000, proxies /api → 8000)
# =============================================================================

set -e

PGDATA="$HOME/.pg_data"
PGPORT=5432
DB_NAME="nexus_sandbox"
DB_USER="nexus"
DB_PASSWORD="nexus"

echo "🌐 Nexus Global Payments Sandbox — Full Stack"
echo "=============================================="

# ── Step 1: PostgreSQL ───────────────────────────────────────────────────────
if [ ! -d "$PGDATA" ]; then
  echo "📦 Initializing PostgreSQL..."
  initdb -D "$PGDATA" --no-locale --encoding=UTF8
  # Allow local password auth
  sed -i 's/trust$/md5/' "$PGDATA/pg_hba.conf"
  echo "local all all trust" >> "$PGDATA/pg_hba.conf"
fi

if ! pg_isready -h localhost -p $PGPORT > /dev/null 2>&1; then
  echo "🐘 Starting PostgreSQL..."
  pg_ctl -D "$PGDATA" -l "$HOME/.pg.log" -o "-p $PGPORT -k /tmp" start
  sleep 2
fi

# Create user and database
psql -h /tmp -p $PGPORT -U $(whoami) -tc \
  "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" postgres 2>/dev/null | grep -q 1 || \
  psql -h /tmp -p $PGPORT -U $(whoami) -c \
  "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" postgres 2>/dev/null

psql -h /tmp -p $PGPORT -U $(whoami) -tc \
  "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" postgres 2>/dev/null | grep -q 1 || \
  psql -h /tmp -p $PGPORT -U $(whoami) -c \
  "CREATE DATABASE $DB_NAME OWNER $DB_USER;" postgres 2>/dev/null

psql -h /tmp -p $PGPORT -U $(whoami) -c \
  "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" postgres 2>/dev/null || true

echo "✅ PostgreSQL ready on port $PGPORT"

# ── Step 2: Run migrations ──────────────────────────────────────────────────
echo "🗄️  Running migrations..."
for f in $(ls migrations/*.sql 2>/dev/null | sort); do
  echo "   → $(basename $f)"
  PGPASSWORD=$DB_PASSWORD psql -h /tmp -p $PGPORT -U $DB_USER -d $DB_NAME -f "$f" 2>/dev/null || true
done
echo "✅ Migrations complete"

# ── Step 3: Redis ────────────────────────────────────────────────────────────
if ! redis-cli ping > /dev/null 2>&1; then
  echo "🔴 Starting Redis..."
  redis-server --daemonize yes --port 6379 --loglevel warning
fi
echo "✅ Redis ready"

# ── Step 4: Python backend ──────────────────────────────────────────────────
echo "🐍 Installing backend dependencies..."
cd services/nexus-gateway
pip install -q -e "." 2>&1 | tail -1
cd ../..

export DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@localhost:$PGPORT/$DB_NAME"
export REDIS_URL="redis://localhost:6379"
export JWT_SECRET="replit-dev-secret"
export QUOTE_VALIDITY_SECONDS=600
export PAYMENT_TIMEOUT_SECONDS=60
export PYTHONPATH="$(pwd)/services/nexus-gateway"

echo "🚀 Starting backend on port 8000..."
cd services/nexus-gateway
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ../..
sleep 2

# ── Step 5: Frontend ─────────────────────────────────────────────────────────
echo "⚙️  Installing frontend dependencies..."
cd services/demo-dashboard
npm install --silent 2>/dev/null

echo ""
echo "=============================================="
echo "🚀 Nexus Sandbox is running!"
echo "   Dashboard: port 3000 (mapped to external 80)"
echo "   API:       port 8000"
echo "   API Docs:  http://localhost:8000/docs"
echo "   PostgreSQL: localhost:$PGPORT/$DB_NAME"
echo "=============================================="
echo ""

# Start frontend (foreground)
npx vite --host 0.0.0.0 --port 3000

# Cleanup
kill $BACKEND_PID 2>/dev/null
