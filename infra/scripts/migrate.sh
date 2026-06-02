#!/usr/bin/env bash
# ============================================================
# DeskForge — Database Migration Runner
# ============================================================
# Usage:
#   bash infra/scripts/migrate.sh              # Run all pending migrations
#   bash infra/scripts/migrate.sh --revision   # Create new migration
#   bash infra/scripts/migrate.sh --status     # Check migration status
#   bash infra/scripts/migrate.sh --history    # Show migration history
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="$(cd "${SCRIPT_DIR}/../../apps/api" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if alembic is available
if ! command -v alembic &> /dev/null; then
    if [ -f "${API_DIR}/.venv/bin/alembic" ]; then
        ALEMBIC="${API_DIR}/.venv/bin/alembic"
    else
        log_error "alembic not found. Install it with: pip install alembic"
        exit 1
    fi
else
    ALEMBIC="alembic"
fi

cd "${API_DIR}"

# Wait for database to be ready
wait_for_db() {
    local max_attempts=30
    local attempt=1

    log_info "Waiting for database to be ready..."

    while [ $attempt -le $max_attempts ]; do
        if $ALEMBIC current &> /dev/null; then
            log_info "Database is ready"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done

    log_error "Database not ready after ${max_attempts} seconds"
    exit 1
}

# Run migrations
run_migrations() {
    log_info "Running pending migrations..."

    # Get current revision before migration
    current_before=$($ALEMBIC current 2>/dev/null || echo "none")
    log_info "Current revision: ${current_before}"

    # Run upgrade
    $ALEMBIC upgrade head

    # Get revision after migration
    current_after=$($ALEMBIC current 2>/dev/null || echo "none")

    if [ "$current_before" = "$current_after" ]; then
        log_info "No pending migrations"
    else
        log_info "Migrations applied successfully"
        log_info "Current revision: ${current_after}"
    fi
}

# Create new migration
create_migration() {
    local message="${1:-}"

    if [ -z "$message" ]; then
        log_error "Migration message required. Usage: $0 --revision 'description'"
        exit 1
    fi

    log_info "Creating new migration: ${message}"
    $ALEMBIC revision --autogenerate -m "$message"
    log_info "Migration created. Review the file before applying."
}

# Show migration status
show_status() {
    log_info "Migration status:"
    echo ""
    echo "Current revision:"
    $ALEMBIC current --verbose 2>/dev/null || echo "  No migrations applied"
    echo ""
    echo "Pending migrations:"
    $ALEMBIC history --verbose 2>/dev/null | head -20 || echo "  None"
}

# Show migration history
show_history() {
    log_info "Migration history:"
    $ALEMBIC history --verbose 2>/dev/null | head -50 || echo "  No migrations found"
}

# Main
case "${1:-}" in
    --revision|-r)
        shift
        create_migration "$*"
        ;;
    --status|-s)
        show_status
        ;;
    --history|-h)
        show_history
        ;;
    *)
        wait_for_db
        run_migrations
        ;;
esac
