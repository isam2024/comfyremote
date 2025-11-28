#!/bin/bash

#######################################
# RunPod ComfyUI WebUI Launcher
# Starts both backend and frontend servers
#######################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo ""
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   RunPod ComfyUI WebUI Launcher       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

#######################################
# Check Prerequisites
#######################################

log_info "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
log_success "Python ${PYTHON_VERSION} found"

# Check Node.js
if ! command -v node &> /dev/null; then
    log_error "Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

NODE_VERSION=$(node --version)
log_success "Node.js ${NODE_VERSION} found"

# Check npm
if ! command -v npm &> /dev/null; then
    log_error "npm is not installed. Please install npm."
    exit 1
fi

NPM_VERSION=$(npm --version)
log_success "npm ${NPM_VERSION} found"

#######################################
# Backend Setup
#######################################

log_info "Setting up backend..."

cd "$BACKEND_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    log_warning "Virtual environment not found. Creating..."
    python3 -m venv venv
    log_success "Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate

# Check if dependencies are installed
if [ ! -f "venv/.dependencies_installed" ]; then
    log_info "Installing backend dependencies..."
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    touch venv/.dependencies_installed
    log_success "Backend dependencies installed"
else
    log_success "Backend dependencies already installed"
fi

# Check for .env file
if [ ! -f ".env" ]; then
    log_warning ".env file not found"

    if [ -f "../.env.template" ]; then
        log_info "Creating .env from template..."
        cp ../.env.template .env
        log_warning "⚠️  Please edit backend/.env and add your RUNPOD_API_KEY"
        log_warning "⚠️  Get your API key from: https://www.runpod.io/console/user/settings"
        echo ""
        read -p "Press Enter after setting your API key in backend/.env..."
    else
        log_error ".env.template not found. Please create backend/.env manually."
        exit 1
    fi
fi

# Validate API key
if ! grep -q "RUNPOD_API_KEY=.*[a-zA-Z0-9]" .env; then
    log_error "RUNPOD_API_KEY not set in backend/.env"
    log_error "Please add your RunPod API key to backend/.env"
    exit 1
fi

log_success "Backend setup complete"

#######################################
# Frontend Setup
#######################################

log_info "Setting up frontend..."

cd "$FRONTEND_DIR"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    log_info "Installing frontend dependencies..."
    npm install -q
    log_success "Frontend dependencies installed"
else
    log_success "Frontend dependencies already installed"
fi

#######################################
# Start Servers
#######################################

echo ""
log_info "Starting servers..."
echo ""

# Create log directory
mkdir -p "$PROJECT_ROOT/logs"

# Start backend in background
cd "$BACKEND_DIR"
log_info "Starting backend server on http://localhost:1445"
source venv/bin/activate
python server.py > "$PROJECT_ROOT/logs/backend.log" 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check if backend is running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    log_error "Backend failed to start. Check logs/backend.log for details."
    cat "$PROJECT_ROOT/logs/backend.log"
    exit 1
fi

log_success "Backend started (PID: $BACKEND_PID)"

# Start frontend in background
cd "$FRONTEND_DIR"
log_info "Starting frontend server on http://localhost:5173"
npm run dev > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 5

# Check if frontend is running
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    log_error "Frontend failed to start. Check logs/frontend.log for details."
    cat "$PROJECT_ROOT/logs/frontend.log"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

log_success "Frontend started (PID: $FRONTEND_PID)"

#######################################
# Display Info
#######################################

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   🚀 Application is running!          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BLUE}Frontend:${NC}  http://localhost:5173"
echo -e "  ${BLUE}Backend:${NC}   http://localhost:1445"
echo -e "  ${BLUE}Health:${NC}    http://localhost:1445/api/health"
echo ""
echo -e "  ${YELLOW}Logs:${NC}"
echo -e "    Backend:  logs/backend.log"
echo -e "    Frontend: logs/frontend.log"
echo ""
echo -e "  ${YELLOW}To view logs in real-time:${NC}"
echo -e "    tail -f logs/backend.log"
echo -e "    tail -f logs/frontend.log"
echo ""
echo -e "${BLUE}Press Ctrl+C to stop all servers${NC}"
echo ""

#######################################
# Cleanup Function
#######################################

cleanup() {
    echo ""
    log_info "Shutting down servers..."

    # Kill backend
    if kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID
        log_success "Backend stopped"
    fi

    # Kill frontend
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID
        log_success "Frontend stopped"
    fi

    # Kill any remaining node/python processes from this script
    pkill -P $$ 2>/dev/null || true

    echo ""
    log_success "All servers stopped. Goodbye!"
    echo ""
    exit 0
}

# Register cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT

#######################################
# Wait for user interrupt
#######################################

# Keep script running
while true; do
    # Check if processes are still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        log_error "Backend process died unexpectedly"
        log_error "Check logs/backend.log for details"
        cat "$PROJECT_ROOT/logs/backend.log"
        exit 1
    fi

    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        log_error "Frontend process died unexpectedly"
        log_error "Check logs/frontend.log for details"
        cat "$PROJECT_ROOT/logs/frontend.log"
        exit 1
    fi

    sleep 2
done
