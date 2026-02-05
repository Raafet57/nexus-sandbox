#!/bin/bash
# =============================================================================
# Nexus Sandbox - One-Command Startup
# Created by Siva Subramanian | https://sivasub.com
# =============================================================================

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}║     ${BOLD}NEXUS SANDBOX${NC}${BLUE}                                         ║${NC}"
echo -e "${BLUE}║     Cross-Border Instant Payments Demo                       ║${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}║     Educational project by Siva Subramanian                  ║${NC}"
echo -e "${BLUE}║     Reference: docs.nexusglobalpayments.org                  ║${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed.${NC}"
    echo "Please install Docker Desktop from https://docker.com/get-started"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}Error: Docker daemon is not running.${NC}"
    echo "Please start Docker Desktop and try again."
    exit 1
fi

# Parse command line arguments
ACTION=${1:-"start"}

case $ACTION in
    start)
        echo -e "${YELLOW}🚀 Starting Nexus Sandbox...${NC}"
        echo ""
        
        # Start services
        docker compose up -d --build
        
        echo ""
        echo -e "${GREEN}✓ All services are starting!${NC}"
        echo ""
        echo -e "${BOLD}Access Points:${NC}"
        echo -e "  📊 ${GREEN}Dashboard:${NC}       http://localhost:8080"
        echo -e "  📖 ${GREEN}API Docs:${NC}        http://localhost:8080/api/docs"
        echo -e "  📜 ${GREEN}ReDoc:${NC}           http://localhost:8080/api/redoc"
        echo -e "  📈 ${GREEN}Jaeger Tracing:${NC}  http://localhost:16686"
        echo ""
        echo -e "${YELLOW}Tip:${NC} Run './start.sh logs' to see live logs"
        echo -e "${YELLOW}Tip:${NC} Run './start.sh stop' to stop all services"
        echo ""
        ;;
    
    stop)
        echo -e "${YELLOW}🛑 Stopping Nexus Sandbox...${NC}"
        docker compose down
        echo -e "${GREEN}✓ All services stopped.${NC}"
        ;;
    
    restart)
        echo -e "${YELLOW}🔄 Restarting Nexus Sandbox...${NC}"
        docker compose down
        docker compose up -d --build
        echo -e "${GREEN}✓ All services restarted.${NC}"
        ;;
    
    logs)
        echo -e "${YELLOW}📋 Showing logs (Ctrl+C to exit)...${NC}"
        docker compose logs -f
        ;;
    
    status)
        echo -e "${YELLOW}📊 Service Status:${NC}"
        docker compose ps
        ;;
    
    clean)
        echo -e "${RED}🧹 Cleaning up all data and images...${NC}"
        docker compose down -v --rmi local
        echo -e "${GREEN}✓ Cleanup complete.${NC}"
        ;;
    
    *)
        echo "Usage: ./start.sh [command]"
        echo ""
        echo "Commands:"
        echo "  start    Start all services (default)"
        echo "  stop     Stop all services"
        echo "  restart  Restart all services"
        echo "  logs     Show live logs"
        echo "  status   Show service status"
        echo "  clean    Clean up data and images"
        ;;
esac
