#!/bin/bash
set -e

# =============================================================================
# Contaixt Backend Deploy Script
# =============================================================================
# Run this after ANY backend changes. It handles:
#   - Rebuilding containers (picks up new dependencies)
#   - Running database migrations
#   - Restarting services
#   - Health checks
#
# Usage:
#   ./deploy.sh          # Full deploy
#   ./deploy.sh --quick  # Skip rebuild (code-only changes)
# =============================================================================

cd "$(dirname "$0")"

QUICK_MODE=false
if [[ "$1" == "--quick" ]]; then
    QUICK_MODE=true
fi

echo "========================================"
echo "  Contaixt Backend Deploy"
echo "========================================"
echo ""

# -----------------------------------------------------------------------------
# Step 1: Rebuild containers (installs new dependencies)
# -----------------------------------------------------------------------------
if [[ "$QUICK_MODE" == false ]]; then
    echo "[1/5] Rebuilding containers..."
    docker compose build api worker
    echo "      Done."
else
    echo "[1/5] Skipping rebuild (--quick mode)"
fi
echo ""

# -----------------------------------------------------------------------------
# Step 2: Start/restart services
# -----------------------------------------------------------------------------
echo "[2/5] Starting services..."
docker compose up -d api worker postgres
echo "      Done."
echo ""

# -----------------------------------------------------------------------------
# Step 3: Wait for API to be healthy
# -----------------------------------------------------------------------------
echo "[3/5] Waiting for API to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0
until docker compose exec -T api curl -sf http://localhost:8000/v1/health > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [[ $RETRY_COUNT -ge $MAX_RETRIES ]]; then
        echo "      ERROR: API failed to start. Check logs:"
        echo "      docker compose logs api --tail=50"
        exit 1
    fi
    echo "      Waiting... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done
echo "      API is healthy."
echo ""

# -----------------------------------------------------------------------------
# Step 4: Run database migrations
# -----------------------------------------------------------------------------
echo "[4/5] Running database migrations..."
docker compose exec -T api alembic upgrade head
echo "      Done."
echo ""

# -----------------------------------------------------------------------------
# Step 5: Restart worker (picks up any schema changes)
# -----------------------------------------------------------------------------
echo "[5/5] Restarting worker..."
docker compose restart worker
echo "      Done."
echo ""

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
echo "========================================"
echo "  Deploy Complete!"
echo "========================================"
echo ""
echo "Services:"
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || docker compose ps
echo ""
echo "Quick test:"
echo "  curl http://localhost:8000/v1/health"
echo ""
echo "View logs:"
echo "  docker compose logs -f api worker"
echo ""
