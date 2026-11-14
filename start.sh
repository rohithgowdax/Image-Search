#!/bin/bash
# VisualSearch — Quick Start Script

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║   VisualSearch — Image Search Engine  ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker not found. Please install Docker Desktop.${NC}"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker Compose v2 not found.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker detected${NC}"

echo ""
echo "🚀 Starting VisualSearch..."
echo "   (First run downloads CLIP model ~600MB — please wait)"
echo ""

docker compose up --build -d

echo ""
echo -e "${GREEN}✅ VisualSearch is running!${NC}"
echo ""
echo "   🌐 App:   http://localhost:3000"
echo "   📡 API:   http://localhost:8000"
echo "   📖 Docs:  http://localhost:8000/api/docs"
echo ""
echo "   To seed sample demo images:"
echo "   docker compose exec backend python scripts/seed_images.py"
echo ""
echo "   To stop:"
echo "   docker compose down"
echo ""
