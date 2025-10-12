#!/bin/bash

# Docker Deployment Startup Script for LLM Sandbox Escape Testing

set -e

echo "========================================"
echo "LLM Sandbox Escape Testing Framework"
echo "Docker Deployment"
echo "========================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker Compose is not installed"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✓ Docker found: $(docker --version)"
echo "✓ Docker Compose found: $(docker-compose --version)"
echo ""

# Check for GOOGLE_API_KEY
if [ -z "$GOOGLE_API_KEY" ] && [ ! -f .env ]; then
    echo "⚠️  Warning: GOOGLE_API_KEY not found"
    echo ""
    echo "Please set your API key:"
    echo "  Option 1: export GOOGLE_API_KEY='your_key_here'"
    echo "  Option 2: Create a .env file with GOOGLE_API_KEY=your_key_here"
    echo ""
    read -p "Do you want to continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if .env exists
if [ -f .env ]; then
    echo "✓ Found .env file"
    # Check if GOOGLE_API_KEY is set in .env
    if grep -q "GOOGLE_API_KEY=" .env; then
        echo "✓ GOOGLE_API_KEY found in .env"
    fi
fi

# Check if GOOGLE_API_KEY is exported
if [ -n "$GOOGLE_API_KEY" ]; then
    echo "✓ GOOGLE_API_KEY found in environment"
fi

echo ""

# Parse command line arguments
DETACHED=""
BUILD_FLAG="--build"
COMMAND="up"

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--detached)
            DETACHED="-d"
            shift
            ;;
        --no-build)
            BUILD_FLAG=""
            shift
            ;;
        down)
            COMMAND="down"
            shift
            ;;
        logs)
            COMMAND="logs"
            shift
            ;;
        restart)
            COMMAND="restart"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  -d, --detached   Run in detached mode"
            echo "  --no-build       Don't rebuild images"
            echo "  down             Stop and remove containers"
            echo "  logs             Show container logs"
            echo "  restart          Restart containers"
            exit 1
            ;;
    esac
done

if [ "$COMMAND" = "up" ]; then
    echo "Starting Docker containers..."
    echo ""
    echo "This will:"
    echo "  1. Build/rebuild Docker images (if needed)"
    echo "  2. Start MCP Server (port 8000)"
    echo "  3. Start LangGraph Agent + UI (ports 8123, 8080)"
    echo ""

    if [ -n "$DETACHED" ]; then
        echo "Running in detached mode..."
        docker-compose up $DETACHED $BUILD_FLAG
        echo ""
        echo "✓ Containers started successfully!"
        echo ""
        echo "Access points:"
        echo "  - Web UI: http://localhost:8080"
        echo "  - API Docs: http://localhost:8123/docs"
        echo "  - MCP Server: http://localhost:8000"
        echo ""
        echo "View logs:"
        echo "  docker-compose logs -f"
        echo ""
        echo "Stop containers:"
        echo "  docker-compose down"
    else
        echo "Running in foreground mode (Ctrl+C to stop)..."
        echo ""
        docker-compose up $BUILD_FLAG
    fi
elif [ "$COMMAND" = "down" ]; then
    echo "Stopping containers..."
    docker-compose down
    echo "✓ Containers stopped"
elif [ "$COMMAND" = "logs" ]; then
    docker-compose logs -f
elif [ "$COMMAND" = "restart" ]; then
    echo "Restarting containers..."
    docker-compose restart
    echo "✓ Containers restarted"
fi
