#!/bin/bash

# Google SERP Data Extractor Tool - Setup Script for macOS
# This script automates the installation and configuration process for non-technical users

set -e  # Exit on any error

# Colors for better user experience
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${PURPLE}================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}================================${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        print_status "Found Python $PYTHON_VERSION"
        
        # Check if version is 3.8 or higher
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
            return 0
        else
            print_error "Python 3.8 or higher is required. Found: $PYTHON_VERSION"
            return 1
        fi
    else
        print_error "Python 3 is not installed"
        return 1
    fi
}

# Function to install Python via Homebrew
install_python() {
    print_status "Installing Python via Homebrew..."
    
    if ! command_exists brew; then
        print_status "Installing Homebrew first..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Add Homebrew to PATH for Apple Silicon Macs
        if [[ $(uname -m) == "arm64" ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
    fi
    
    brew install python3
    print_success "Python installed successfully"
}

# Function to create virtual environment
create_venv() {
    print_status "Creating Python virtual environment..."
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists. Removing old one..."
        rm -rf venv
    fi
    
    python3 -m venv venv
    print_success "Virtual environment created"
}

# Function to activate virtual environment
activate_venv() {
    print_status "Activating virtual environment..."
    source venv/bin/activate
    print_success "Virtual environment activated"
}

# Function to install dependencies
install_dependencies() {
    print_status "Installing required dependencies..."
    
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found!"
        exit 1
    fi
    
    pip install --upgrade pip
    pip install -r requirements.txt
    print_success "Dependencies installed successfully"
}

# Function to create .env file
create_env_file() {
    print_status "Setting up configuration..."
    
    if [ ! -f ".env" ]; then
        if [ -f "env.example" ]; then
            cp env.example .env
            print_success "Created .env file from template"
        else
            print_error "env.example not found!"
            exit 1
        fi
    else
        print_warning ".env file already exists"
    fi
}

# Function to guide user through API configuration
configure_api() {
    print_header "API Configuration Required"
    echo
    echo "To use this tool, you need to set up your Google Custom Search Engine API:"
    echo
    echo "1. Go to Google Cloud Console: https://console.cloud.google.com/"
    echo "2. Create a new project or select an existing one"
    echo "3. Enable the 'Custom Search JSON API'"
    echo "4. Create credentials (API Key)"
    echo "5. Go to Programmable Search Engine: https://programmablesearchengine.google.com/"
    echo "6. Create a new search engine or use an existing one"
    echo "7. Get your Search Engine ID (CX)"
    echo
    echo "Once you have both values, I'll help you configure them."
    echo
    
    read -p "Do you have your Google API Key and Search Engine ID ready? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        configure_api_keys
    else
        print_warning "You can configure the API keys later by editing the .env file"
        print_status "For now, the tool is installed but not yet configured"
    fi
}

# Function to configure API keys
configure_api_keys() {
    echo
    read -p "Enter your Google API Key: " GOOGLE_API_KEY
    read -p "Enter your Google Search Engine ID (CX): " GOOGLE_CSE_CX
    
    if [ -n "$GOOGLE_API_KEY" ] && [ -n "$GOOGLE_CSE_CX" ]; then
        # Update .env file
        sed -i.bak "s/GOOGLE_API_KEY=/GOOGLE_API_KEY=$GOOGLE_API_KEY/" .env
        sed -i.bak "s/GOOGLE_CSE_CX=/GOOGLE_CSE_CX=$GOOGLE_CSE_CX/" .env
        rm .env.bak
        
        print_success "API keys configured successfully!"
    else
        print_warning "API keys not provided. You can configure them later in the .env file"
    fi
}

# Function to test installation
test_installation() {
    print_status "Testing installation..."
    
    # Test Python import
    if python3 -c "import fastapi, pandas, click" 2>/dev/null; then
        print_success "All required packages are installed"
    else
        print_error "Some packages are missing. Please check the installation."
        exit 1
    fi
    
    # Test CLI
    if python3 cli.py --help >/dev/null 2>&1; then
        print_success "CLI is working correctly"
    else
        print_error "CLI test failed"
        exit 1
    fi
}

# Function to create usage guide
create_usage_guide() {
    print_status "Skipping usage guide creation (as requested)"
}

# Main installation process
main() {
    print_header "Google SERP Data Extractor Tool - Setup"
    echo
    print_status "This script will help you install and configure the Google SERP Data Extractor Tool"
    echo
    
    # Check if we're on macOS
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_error "This setup script is designed for macOS. Please use the appropriate setup method for your operating system."
        exit 1
    fi
    
    # Check Python installation
    if ! check_python_version; then
        print_status "Python 3.8+ not found. Installing Python..."
        install_python
        
        # Check again after installation
        if ! check_python_version; then
            print_error "Failed to install Python. Please install Python 3.8+ manually and run this script again."
            exit 1
        fi
    fi
    
    # Create virtual environment
    create_venv
    
    # Activate virtual environment
    activate_venv
    
    # Install dependencies
    install_dependencies
    
    # Create .env file
    create_env_file
    
    # Configure API keys
    configure_api
    
    # Test installation
    test_installation
    
    # Create usage guide
    create_usage_guide
    
    print_header "Installation Complete!"
    echo
    print_success "The Google SERP Data Extractor Tool has been successfully installed!"
    echo
    print_status "Next steps:"
    echo "1. Start the web server using: ./run.sh"
    echo "2. Open your browser to: http://localhost:8000"
    echo "3. Upload your keywords file and start scraping!"
    echo
    print_status "To get started quickly:"
    echo "1. Run: ./run.sh"
    echo "2. Open: http://localhost:8000 in your browser"
    echo "3. Upload a keywords file and configure your search settings"
    echo
    print_success "Happy scraping! 🚀"
}

# Run main function
main "$@"
