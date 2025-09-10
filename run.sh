#!/bin/bash

# Google SERP Data Extractor Tool - Web Server Launcher
# This script starts the web server for the Google SERP Data Extractor Tool

# Colors for better user experience
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${PURPLE}================================${NC}"
    echo -e "${PURPLE}Google SERP Data Extractor Tool${NC}"
    echo -e "${PURPLE}Web Server Launcher${NC}"
    echo -e "${PURPLE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to find available port
find_available_port() {
    local start_port=$1
    local port=$start_port
    
    while check_port $port; do
        port=$((port + 1))
        if [ $port -gt $((start_port + 100)) ]; then
            print_error "Could not find an available port starting from $start_port"
            exit 1
        fi
    done
    
    echo $port
}

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

print_header

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found. Please run ./setup.sh first."
    exit 1
fi

# Check if API keys are configured
if ! grep -q "GOOGLE_API_KEY=.*[^[:space:]]" .env || ! grep -q "GOOGLE_CSE_CX=.*[^[:space:]]" .env; then
    print_warning "API keys not configured. The web interface will start but scraping may not work."
    print_info "To configure API keys, edit the .env file with your Google API credentials."
    echo
    read -p "Do you want to continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Please run ./setup.sh to configure your API keys first."
        exit 1
    fi
fi

# Check if required packages are installed
print_info "Checking dependencies..."
if ! python3 -c "import fastapi, uvicorn" 2>/dev/null; then
    print_error "Required packages not found. Please run ./setup.sh first."
    exit 1
fi

# Set default port
DEFAULT_PORT=8000
PORT=${1:-$DEFAULT_PORT}

# Check if port is available
if check_port $PORT; then
    print_warning "Port $PORT is already in use."
    NEW_PORT=$(find_available_port $PORT)
    print_info "Using port $NEW_PORT instead."
    PORT=$NEW_PORT
fi

print_success "Starting Google SERP Data Extractor Web Server..."
echo
print_info "Server will be available at:"
echo -e "${CYAN}  http://localhost:$PORT${NC}"
echo -e "${CYAN}  http://127.0.0.1:$PORT${NC}"
echo
print_info "Press Ctrl+C to stop the server"
echo

# Start the web server
python3 app.py --port $PORT 2>/dev/null || {
    # If app.py doesn't support --port, use uvicorn directly
    print_info "Starting server with uvicorn..."
    uvicorn serp_tool.web.app:app --host 0.0.0.0 --port $PORT --reload
}
