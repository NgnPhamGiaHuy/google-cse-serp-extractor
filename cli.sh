#!/bin/bash

# Google SERP Data Extractor Tool - CLI Launcher
# This script runs the command-line interface for the Google SERP Data Extractor Tool

# Colors for better user experience
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}Google SERP Data Extractor Tool${NC}"
    echo -e "${BLUE}Command Line Interface${NC}"
    echo -e "${BLUE}================================${NC}"
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

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

print_header

# Check if arguments were provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <keywords_file> <output_file> [options]"
    echo
    echo "Examples:"
    echo "  $0 keywords.txt results.xlsx"
    echo "  $0 keywords.txt results.csv --include-paa --include-related"
    echo "  $0 example_keywords.txt results.xlsx --max-pages 2"
    echo
    echo "Available options:"
    echo "  --max-pages N          Maximum pages to scrape (default: 10)"
    echo "  (results per page fixed to 10 by Google CSE)"
    echo "  --include-organic      Include organic results (default: true)"
    echo "  --include-paa          Include People Also Ask"
    echo "  --include-related      Include related searches"
    echo "  --include-ads          Include ads"
    echo "  --include-ai-overview  Include AI overview"
    echo
    echo "For more help, run: python cli.py --help"
    echo
    echo "💡 Tip: For a web interface, use: ./run.sh"
    exit 1
fi

# Check if keywords file exists
if [ ! -f "$1" ]; then
    print_error "Keywords file '$1' not found!"
    echo "Available example files:"
    ls -1 *.txt 2>/dev/null || echo "  No .txt files found"
    exit 1
fi

# Check if .env file exists and has API keys
if [ ! -f ".env" ]; then
    print_error ".env file not found. Please run ./setup.sh first."
    exit 1
fi

# Check if API keys are configured
if ! grep -q "GOOGLE_API_KEY=.*[^[:space:]]" .env || ! grep -q "GOOGLE_CSE_CX=.*[^[:space:]]" .env; then
    print_warning "API keys not configured. Please edit .env file with your Google API credentials."
    echo "Required: GOOGLE_API_KEY and GOOGLE_CSE_CX"
    exit 1
fi

# Run the CLI with all arguments
print_success "Running Google SERP Data Extractor CLI..."
echo "Keywords file: $1"
echo "Output file: $2"
echo

python cli.py "$@"

if [ $? -eq 0 ]; then
    print_success "Scraping completed successfully!"
    echo "Results saved to: $2"
else
    print_error "Scraping failed. Check the error messages above."
    exit 1
fi
