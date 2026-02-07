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

# Check for port conflicts
echo -e "${YELLOW}Checking for port conflicts...${NC}"

PORTS=("5432" "6379" "8000" "8080" "16686" "9092" "2181" "4317" "4318")
PORT_NAMES=("PostgreSQL" "Redis" "Nexus Gateway" "Dashboard" "Jaeger" "Kafka" "Zookeeper" "OTLP HTTP" "OTLP GRPC")
CONFLICTS=false

for i in "${!PORTS[@]}"; do
    PORT=${PORTS[$i]}
    NAME=${PORT_NAMES[$i]}

    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 || netstat -an 2>/dev/null | grep "\.$PORT " | grep LISTEN >/dev/null 2>&1; then
        echo -e "  ${RED}✗ Port $PORT ($NAME) is already in use${NC}"
        CONFLICTS=true
    else
        echo -e "  ${GREEN}✓ Port $PORT ($NAME) is available${NC}"
    fi
done

if [ "$CONFLICTS" = true ]; then
    echo ""
    echo -e "${YELLOW}Warning: Some ports are already in use.${NC}"
    echo "This may cause services to fail. Options:"
    echo "  1. Stop the conflicting services"
    echo "  2. Use 'lite' mode: ./start.sh lite (uses fewer ports)"
    echo "  3. Modify port mappings in docker-compose.yml"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Startup cancelled."
        exit 1
    fi
fi

echo ""

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
    
    lite)
        echo -e "${YELLOW}🚀 Starting Nexus Sandbox (Lite Mode)...${NC}"
        echo -e "${YELLOW}   This mode excludes Kafka, Jaeger, and simulators.${NC}"
        echo ""
        
        # Start lite services
        docker compose -f docker-compose.lite.yml up -d --build
        
        echo ""
        echo -e "${GREEN}✓ Lite services are starting!${NC}"
        echo ""
        echo -e "${BOLD}Access Points:${NC}"
        echo -e "  📊 ${GREEN}Dashboard:${NC}       http://localhost:8080"
        echo -e "  📖 ${GREEN}API Docs:${NC}        http://localhost:8080/api/docs"
        echo -e "  📜 ${GREEN}ReDoc:${NC}           http://localhost:8080/api/redoc"
        echo ""
        echo -e "${YELLOW}Note:${NC} Jaeger tracing is disabled in lite mode"
        echo -e "${YELLOW}Tip:${NC}  Run './start.sh logs-lite' to see live logs"
        echo ""
        ;;
    
    stop)
        echo -e "${YELLOW}🛑 Stopping Nexus Sandbox...${NC}"
        docker compose down
        docker compose -f docker-compose.lite.yml down 2>/dev/null || true
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
    
    logs-lite)
        echo -e "${YELLOW}📋 Showing lite mode logs (Ctrl+C to exit)...${NC}"
        docker compose -f docker-compose.lite.yml logs -f
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
        echo "  start      Start all services (default) - Full stack with Kafka, Jaeger"
        echo "  lite       Start lite mode - Faster startup (~20s), no Kafka/Jaeger"
        echo "  stop       Stop all services"
        echo "  restart    Restart all services"
        echo "  logs       Show live logs (full stack)"
        echo "  logs-lite  Show live logs (lite mode)"
        echo "  status     Show service status"
        echo "  clean      Clean up data and images"
        ;;
esac
