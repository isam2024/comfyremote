#!/bin/bash

#######################################
# RunPod ComfyUI WebUI - Stop Script
# Stops all running servers
#######################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

echo ""
log_info "Stopping RunPod ComfyUI WebUI servers..."

# Find and kill Python backend processes
BACKEND_PIDS=$(ps aux | grep "python.*server.py" | grep -v grep | awk '{print $2}')
if [ -n "$BACKEND_PIDS" ]; then
    echo "$BACKEND_PIDS" | xargs kill -9 2>/dev/null
    log_success "Backend server(s) stopped"
else
    log_info "No backend servers running"
fi

# Find and kill Vite frontend processes
FRONTEND_PIDS=$(ps aux | grep "vite" | grep -v grep | awk '{print $2}')
if [ -n "$FRONTEND_PIDS" ]; then
    echo "$FRONTEND_PIDS" | xargs kill -9 2>/dev/null
    log_success "Frontend server(s) stopped"
else
    log_info "No frontend servers running"
fi

# Clean up any node processes from the project
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NODE_PIDS=$(ps aux | grep "node" | grep "$PROJECT_DIR" | grep -v grep | awk '{print $2}')
if [ -n "$NODE_PIDS" ]; then
    echo "$NODE_PIDS" | xargs kill -9 2>/dev/null
    log_success "Node processes cleaned up"
fi

echo ""
log_success "All servers stopped!"
echo ""
