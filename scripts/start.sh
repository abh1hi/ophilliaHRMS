#!/usr/bin/env bash
# Usage: ./scripts/start.sh [profiles...]
# Default: core hr
# Examples:
#   ./scripts/start.sh              -> starts gateway + auth + db + redis + rabbitmq + hr services
#   ./scripts/start.sh core         -> starts gateway + auth + db + redis + rabbitmq only
#   ./scripts/start.sh core payroll -> core + payroll module
set -e
PROFILES=("${@:-core hr}")
PROFILE_ARGS=()
for p in "${PROFILES[@]}"; do PROFILE_ARGS+=(--profile "$p"); done
echo "Starting HRMS with profiles: ${PROFILES[*]}"
docker compose "${PROFILE_ARGS[@]}" up --build -d
echo ""
echo "Gateway: http://localhost/health"
