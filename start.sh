#!/bin/bash

# Start script for Security Researcher Agent
# Provides easy access to different interfaces

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Security Researcher Agent${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check conda environment
if [[ "$CONDA_DEFAULT_ENV" != "lang_sdbx" ]]; then
    echo -e "${YELLOW}⚠ Activating conda environment: lang_sdbx${NC}"
    eval "$(conda shell.bash hook)"
    conda activate lang_sdbx
fi

# Parse command
MODE=${1:-help}

case $MODE in
    cli)
        echo -e "${GREEN}Starting CLI mode...${NC}"
        echo ""
        cd agent
        python workflow.py
        ;;

    api)
        echo -e "${GREEN}Starting API server on http://localhost:8123${NC}"
        echo -e "${BLUE}Endpoints:${NC}"
        echo -e "  - GET  http://localhost:8123/"
        echo -e "  - POST http://localhost:8123/invoke"
        echo -e "  - GET  http://localhost:8123/health"
        echo ""
        cd agent
        python api_server.py
        ;;

    mcp)
        echo -e "${GREEN}Starting MCP server on http://localhost:8000${NC}"
        echo ""
        cd mcp_server
        python server.py
        ;;

    docker)
        echo -e "${GREEN}Building and starting Docker containers...${NC}"
        echo ""
        docker-compose up --build
        ;;

    docker-bg)
        echo -e "${GREEN}Starting Docker containers in background...${NC}"
        echo ""
        docker-compose up -d
        echo ""
        echo -e "${BLUE}View logs:${NC}"
        echo -e "  docker-compose logs -f agent"
        echo -e "  docker-compose logs -f mcp-server"
        ;;

    studio)
        echo -e "${GREEN}Opening LangGraph Studio...${NC}"
        echo ""
        echo -e "${YELLOW}Make sure LangGraph Studio is installed${NC}"
        echo -e "If not installed, download from:"
        echo -e "  https://github.com/langchain-ai/langgraph-studio"
        echo ""
        echo -e "${BLUE}Then open this directory in LangGraph Studio${NC}"
        echo -e "Studio will auto-detect langgraph.json"
        ;;

    test)
        echo -e "${GREEN}Running quick test...${NC}"
        echo ""
        cd agent
        export USE_DIRECT_CLIENT=true
        python workflow.py
        ;;

    install)
        echo -e "${GREEN}Installing dependencies...${NC}"
        echo ""
        cd agent
        pip install -r requirements.txt
        echo ""
        echo -e "${GREEN}✓ Dependencies installed${NC}"
        ;;

    help|*)
        echo "Usage: ./start.sh [mode]"
        echo ""
        echo "Modes:"
        echo "  cli         - Run agent in CLI mode (default experiment)"
        echo "  api         - Start FastAPI server for custom UIs"
        echo "  mcp         - Start MCP server (for remote testing)"
        echo "  docker      - Build and run with Docker Compose"
        echo "  docker-bg   - Run Docker containers in background"
        echo "  studio      - Instructions for LangGraph Studio"
        echo "  test        - Quick test with direct execution"
        echo "  install     - Install Python dependencies"
        echo "  help        - Show this help"
        echo ""
        echo "Examples:"
        echo "  ./start.sh cli          # Run CLI experiment"
        echo "  ./start.sh api          # Start API server"
        echo "  ./start.sh docker       # Run in Docker"
        echo ""
        echo "For more details, see:"
        echo "  - INTERACTIVE_UI.md - UI interaction guide"
        echo "  - DOCKER.md - Docker deployment guide"
        echo "  - README.md - Project overview"
        ;;
esac
