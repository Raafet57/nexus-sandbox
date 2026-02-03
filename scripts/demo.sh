#!/bin/bash
# Nexus Global Payments Sandbox - Demo Launcher
# Usage: ./scripts/demo.sh [up|down|status|logs]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_banner() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║                                                           ║"
    echo "║     🌏  NEXUS GLOBAL PAYMENTS SANDBOX                     ║"
    echo "║         Cross-Border Instant Payments Demo                ║"
    echo "║                                                           ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

cmd_up() {
    print_banner
    echo -e "${YELLOW}Starting Nexus sandbox...${NC}"
    echo ""
    
    docker compose up -d --build
    
    echo ""
    echo -e "${GREEN}✓ Services starting!${NC}"
    echo ""
    echo "Waiting for services to be healthy..."
    sleep 10
    
    cmd_status
    
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  🎉 Sandbox Ready!                                        ║${NC}"
    echo -e "${GREEN}╠═══════════════════════════════════════════════════════════╣${NC}"
    echo -e "${GREEN}║                                                           ║${NC}"
    echo -e "${GREEN}║  📊 Demo Dashboard:    http://localhost:8080              ║${NC}"
    echo -e "${GREEN}║  📚 API Docs:          http://localhost:8000/docs         ║${NC}"
    echo -e "${GREEN}║  🔍 Jaeger Tracing:    http://localhost:16686             ║${NC}"
    echo -e "${GREEN}║                                                           ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
}

cmd_down() {
    print_banner
    echo -e "${YELLOW}Stopping Nexus sandbox...${NC}"
    docker compose down
    echo -e "${GREEN}✓ All services stopped${NC}"
}

cmd_status() {
    echo -e "${BLUE}Service Status:${NC}"
    echo ""
    
    services=("nexus-gateway:8000" "nexus-psp-sg:3001" "nexus-fxp-abc:3201" "nexus-ips-sg:3101")
    
    for svc in "${services[@]}"; do
        name="${svc%%:*}"
        port="${svc##*:}"
        
        if docker ps --format '{{.Names}}' | grep -q "^${name}$"; then
            echo -e "  ${GREEN}✓${NC} ${name} (port ${port})"
        else
            echo -e "  ${RED}✗${NC} ${name}"
        fi
    done
    
    echo ""
    echo -e "${BLUE}Infrastructure:${NC}"
    for infra in "postgres" "redis" "kafka"; do
        if docker ps --format '{{.Names}}' | grep -q "nexus-${infra}"; then
            echo -e "  ${GREEN}✓${NC} ${infra}"
        else
            echo -e "  ${RED}✗${NC} ${infra}"
        fi
    done
}

cmd_logs() {
    docker compose logs -f --tail=100 "$@"
}

cmd_test() {
    print_banner
    echo -e "${YELLOW}Running API health checks...${NC}"
    echo ""
    
    # Gateway
    if curl -sf http://localhost:8000/health > /dev/null; then
        echo -e "${GREEN}✓${NC} Gateway healthy"
    else
        echo -e "${RED}✗${NC} Gateway not responding"
    fi
    
    # PSP SG
    if curl -sf http://localhost:3001/health > /dev/null; then
        echo -e "${GREEN}✓${NC} PSP Singapore healthy"
    else
        echo -e "${RED}✗${NC} PSP Singapore not responding"
    fi
    
    echo ""
    echo -e "${BLUE}Testing sample payment flow...${NC}"
    echo ""
    
    # Sample payment
    RESPONSE=$(curl -sf http://localhost:8000/v1/countries || echo '{"error": true}')
    if echo "$RESPONSE" | grep -q "countries"; then
        echo -e "${GREEN}✓${NC} Countries endpoint working"
    else
        echo -e "${YELLOW}⚠${NC} Countries endpoint returned unexpected response"
    fi
}

cmd_help() {
    print_banner
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  up      Start all sandbox services"
    echo "  down    Stop all services"
    echo "  status  Check service health"
    echo "  logs    Follow service logs"
    echo "  test    Run API health checks"
    echo "  help    Show this help"
    echo ""
}

# Main
case "${1:-help}" in
    up)      cmd_up ;;
    down)    cmd_down ;;
    status)  cmd_status ;;
    logs)    cmd_logs "${@:2}" ;;
    test)    cmd_test ;;
    *)       cmd_help ;;
esac
