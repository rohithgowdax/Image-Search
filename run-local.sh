#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║   VisualSearch — Image Search Engine  ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

# Check for uv
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}⚠️  'uv' not found in PATH.${NC}"
    echo "   Please install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "   or via Homebrew: brew install uv"
    exit 1
fi

echo -e "${GREEN}✓ Found uv: $(uv --version)${NC}"

# Backend setup
echo -e "\n${BLUE}⚙️  Setting up Backend with uv...${NC}"
cd "$SCRIPT_DIR/backend"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment using uv..."
    uv venv .venv
fi

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "Creating backend .env from .env.example..."
    cp .env.example .env
fi

echo "Installing/verifying backend dependencies..."
uv pip install -r requirements.txt

# Start backend
echo -e "${GREEN}🚀 Starting Backend on http://localhost:8000 ...${NC}"
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Frontend setup
echo -e "\n${BLUE}⚙️  Setting up Frontend...${NC}"
cd "$SCRIPT_DIR/frontend"

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Start frontend
echo -e "${GREEN}🚀 Starting Frontend on http://localhost:3000 ...${NC}"
npm start &
FRONTEND_PID=$!

# Trap cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down servers...${NC}"
    kill "$BACKEND_PID" 2>/dev/null || true
    kill "$FRONTEND_PID" 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  VisualSearch is running locally!${NC}"
echo -e "  Frontend : http://localhost:3000"
echo -e "  Backend  : http://localhost:8000"
echo -e "  API Docs : http://localhost:8000/api/docs"
echo -e "${GREEN}========================================${NC}"
echo "Press Ctrl+C to stop both servers."

wait
