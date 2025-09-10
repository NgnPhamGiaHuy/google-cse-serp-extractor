# 🔍 Google CSE SERP Extractor

[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge&logo=opensourceinitiative&logoColor=white)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen?style=for-the-badge)]()

A **production-ready, enterprise-grade** Google Search Engine Results Page (SERP) data extraction tool that leverages Google's Custom Search Engine API to scrape search results at scale. Built with modern Python technologies, this tool provides both a powerful CLI interface and an intuitive web application for bulk keyword research, competitive analysis, and SEO data collection.

---

## 📋 Description

The Google CSE SERP Extractor is designed for **digital marketers, SEO professionals, data analysts, and researchers** who need reliable, scalable access to Google search results data. Unlike web scraping approaches that risk IP blocking and rate limiting, this tool uses Google's official Custom Search Engine API to deliver **consistent, accurate, and compliant** search data extraction.

**Key Value Propositions:**
- **100% API-based approach** eliminates IP blocking risks and ensures data accuracy
- **Bulk processing capabilities** handle thousands of keywords efficiently with intelligent rate limiting
- **Multi-format support** for input (CSV, Excel, JSON) and output (JSON, CSV, Excel) with seamless data transformation
- **Advanced filtering options** including profile site targeting, query normalization, and duplicate detection
- **Production-grade architecture** with comprehensive error handling, logging, and quota management

The tool processes **10-100 results per keyword** across **1-3 pages** with configurable pagination, delivering structured data that includes titles, URLs, snippets, positions, and metadata. Built-in caching mechanisms and intelligent delay systems ensure optimal API usage while maintaining high throughput for large-scale data collection projects.

---

## ✨ Key Benefits and Features

### 🚀 **High-Performance Data Extraction**
Process thousands of keywords efficiently with intelligent batching, automatic retry mechanisms, and smart rate limiting. The tool handles up to **100 results per keyword** across multiple pages, delivering comprehensive search result datasets in minutes rather than hours.

### 🎯 **Advanced Query Targeting**
Target specific platforms and domains using intelligent site filtering. The built-in platform suggestion system supports **50+ popular platforms** (LinkedIn, GitHub, Twitter, etc.) with automatic query transformation, enabling precise profile and content discovery across professional networks.

### 📊 **Flexible Data Management**
Support for multiple input formats (CSV, Excel, JSON) and output formats (JSON, CSV, Excel) with automatic data validation and transformation. The unified schema ensures consistent data structure regardless of input source, making integration with existing workflows seamless.

### 🔧 **Production-Ready Architecture**
Enterprise-grade error handling, comprehensive logging, and quota management ensure reliable operation at scale. Built-in caching reduces API costs, while automatic cleanup and resource management prevent system resource exhaustion during long-running operations.

### 🌐 **Dual Interface Design**
Choose between a powerful CLI for automation and scripting, or an intuitive web interface for interactive use. Both interfaces share the same robust backend, ensuring consistent results regardless of your preferred workflow.

### 🔒 **Secure Token Management**
Advanced token management with backup API key support, automatic quota detection, and secure temporary storage. The system automatically switches to backup tokens when quota limits are reached, ensuring uninterrupted operation.

---

## 🚀 Installation

### Prerequisites
- **Python 3.8+** (Python 3.9+ recommended for optimal performance)
- **Google Cloud Console** account with Custom Search Engine API enabled
- **Google Custom Search Engine** configured with appropriate search settings

### Quick Setup (macOS)

```bash
# Clone the repository
git clone https://github.com/NgnPhamGiaHuy/google-cse-serp-extractor.git
cd google-cse-serp-extractor

# Run the automated setup script
chmod +x setup.sh
./setup.sh
```

The setup script will:
- ✅ Check Python version and install if needed
- ✅ Create a virtual environment
- ✅ Install all dependencies
- ✅ Generate configuration files
- ✅ Test the installation

### Manual Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create configuration file
cp env.example .env
```

### Environment Configuration

Create a `.env` file with your Google API credentials:

```bash
# Google Custom Search Engine API
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_CSE_CX=your_custom_search_engine_id_here

# Optional: Backup API keys for quota management
GOOGLE_API_KEY_BACKUP=your_backup_api_key_here
GOOGLE_CX_BACKUP=your_backup_cse_id_here
```

---

## 💻 Usage

### Web Interface (Recommended)

Start the web application using the convenient launcher script:

```bash
# Using the launcher script (recommended)
./run.sh

# Or manually
python app.py
```

The launcher script will:
- ✅ Check for virtual environment and dependencies
- ✅ Validate API key configuration
- ✅ Find an available port if 8000 is occupied
- ✅ Start the web server with proper error handling

Navigate to `http://localhost:8000` in your browser for the interactive interface.

**Web Interface Features:**
- 📁 **File Upload**: Drag-and-drop support for CSV, Excel, and JSON files
- ⌨️ **Manual Queries**: Direct text input with real-time preview
- 🎯 **Platform Targeting**: Visual platform selection with auto-suggestions
- 📊 **Real-time Progress**: Live progress tracking with detailed statistics
- 📈 **Results Visualization**: Interactive results display with filtering
- 💾 **Export Options**: One-click export to JSON, CSV, or Excel formats

### Command Line Interface

#### Basic Usage

```bash
# Single keyword search
python cli.py --keywords "python web scraping" --output results.json

# Multiple keywords from file
python cli.py --keywords keywords.csv --output results.xlsx --max-pages 3

# Advanced filtering with platform targeting
python cli.py --keywords keywords.json --output results.csv \
  --profile-site "site:linkedin.com/in" \
  --profile-site "site:github.com" \
  --results-per-page 50
```

#### Advanced Options

```bash
# Full configuration example
python cli.py \
  --keywords data/keywords.xlsx \
  --output results/search_results_$(date +%Y%m%d).json \
  --max-pages 3 \
  --results-per-page 100 \
  --include-organic \
  --profile-site "site:linkedin.com/in" \
  --profile-site "site:twitter.com" \
  --allow-duplicates
```

### Configuration Options

| Parameter | Description | Default | Range |
|-----------|-------------|---------|-------|
| `--max-pages` | Maximum pages to scrape per keyword | 3 | 1-10 |
| `--results-per-page` | Results per page | 10 | 10-100 |
| `--include-organic` | Include organic search results | True | Boolean |
| `--include-paa` | Include "People Also Ask" results | False | Boolean |
| `--include-related` | Include related search suggestions | False | Boolean |
| `--include-ads` | Include advertisement results | False | Boolean |
| `--profile-site` | Target specific sites (can be used multiple times) | None | String |
| `--allow-duplicates` | Allow duplicate queries after normalization | False | Boolean |

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `GOOGLE_API_KEY` | Google Custom Search Engine API key | Yes | `AIzaSyB...` |
| `GOOGLE_CSE_CX` | Custom Search Engine ID | Yes | `012345678901234567890:abcdefghijk` |
| `GOOGLE_API_KEY_BACKUP` | Backup API key for quota management | No | `AIzaSyB...` |
| `GOOGLE_CX_BACKUP` | Backup CSE ID | No | `012345678901234567890:xyzabcdef` |

### Configuration File (`config.yaml`)

The tool uses a centralized YAML configuration file for advanced settings:

```yaml
api:
  provider_order: [google]
  google:
    base_url: https://www.googleapis.com/customsearch/v1
    apply_locale_hints: false

search:
  results_per_page: 10
  max_pages: 3
  country: null
  language: null
  device: desktop

behavior:
  max_retries: 2
  delay_ms: 1000
  fallback_strategy: sequential

caching:
  enabled: true
  ttl_seconds: 86400
```

---

## 📁 Folder Structure

```
google-cse-serp-extractor/
├── 📁 serp_tool/                    # Core application package
│   ├── 📁 cli/                      # Command-line interface
│   │   ├── main.py                  # CLI entry point and commands
│   │   └── helpers.py               # CLI utility functions
│   ├── 📁 clients/                  # API client implementations
│   │   └── 📁 cse/                  # Google CSE client
│   │       ├── client.py            # Main CSE API client
│   │       ├── cache.py             # Response caching system
│   │       ├── http.py              # HTTP request handling
│   │       └── mapping.py           # Data transformation utilities
│   ├── 📁 handlers/                 # Data processing handlers
│   │   ├── readers.py               # Input file readers (CSV, Excel, JSON)
│   │   ├── writers.py               # Output file writers
│   │   ├── flatteners.py            # Data structure flattening
│   │   └── common.py                # Shared handler utilities
│   ├── 📁 web/                      # Web application
│   │   ├── app.py                   # FastAPI application setup
│   │   ├── routes.py                # API endpoints and routing
│   │   ├── background.py            # Background job processing
│   │   ├── state.py                 # Application state management
│   │   └── helpers.py               # Web utility functions
│   ├── 📁 utils/                    # Utility modules
│   │   ├── query_utils.py           # Query processing and validation
│   │   ├── dedup_utils.py           # Duplicate detection and removal
│   │   ├── platform_utils.py        # Platform name to site filter conversion
│   │   ├── token_manager.py         # API token management
│   │   ├── temp_manager.py          # Temporary file management
│   │   └── delay_utils.py           # Rate limiting and delays
│   └── 📁 logging/                  # Logging system
│       ├── core.py                  # Logging configuration
│       ├── formatter.py             # Log message formatting
│       └── filters.py               # Log filtering utilities
├── 📁 models/                       # Data models and schemas
│   ├── entities.py                  # Core data entities
│   ├── search_config.py             # Search configuration models
│   └── job_status.py                # Job status tracking models
├── 📁 config/                       # Configuration management
│   └── core.py                      # Configuration loading and validation
├── 📁 templates/                    # Web interface templates
│   ├── base.html                    # Base HTML template
│   └── index.html                   # Main application interface
├── 📁 static/                       # Static web assets
│   └── 📁 css/                      # Stylesheets
├── 📁 downloads/                    # Output file directory
├── 📁 logs/                         # Application logs
├── 📄 app.py                        # Web application entry point
├── 📄 cli.py                        # CLI entry point
├── 📄 requirements.txt              # Python dependencies
├── 📄 config.yaml                   # Application configuration
└── 📄 schema.py                     # Type definitions and schemas
```

---

## 🤝 Contributing

We welcome contributions from the community! Here's how you can get started:

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/your-username/google-cse-serp-extractor.git
cd google-cse-serp-extractor

# Create a development environment
python3 -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available

# Install pre-commit hooks
pre-commit install
```

### Contribution Workflow

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the existing code style and patterns

3. **Add tests** for new functionality (if applicable)

4. **Run the test suite**:
   ```bash
   python -m pytest tests/
   ```

5. **Commit your changes** with descriptive commit messages:
   ```bash
   git add .
   git commit -m "feat: add new platform targeting feature"
   ```

6. **Push to your fork** and create a pull request:
   ```bash
   git push origin feature/your-feature-name
   ```

### Code Style Guidelines

- Follow **PEP 8** Python style guidelines
- Use **type hints** for all function parameters and return values
- Write **comprehensive docstrings** for all public functions and classes
- Maintain **test coverage** above 80% for new features
- Use **meaningful variable names** and avoid abbreviations

### Reporting Issues

When reporting bugs or requesting features, please include:
- **Clear description** of the issue or feature request
- **Steps to reproduce** (for bugs)
- **Expected vs. actual behavior**
- **Environment details** (Python version, OS, etc.)
- **Log files** (if applicable)

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

The MIT License allows you to:
- ✅ Use the software commercially
- ✅ Modify and distribute the software
- ✅ Include the software in proprietary applications
- ✅ Use the software privately

---

## 👤 Author

<div align="center">

**NgnPhamGiaHuy**

[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/NgnPhamGiaHuy)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/nguyenphamgiahuy)

</div>

---

## 🙏 Acknowledgements

Special thanks to the following projects and communities that made this tool possible:

- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern, fast web framework for building APIs
- **[Google Custom Search Engine API](https://developers.google.com/custom-search/v1/introduction)** - Official Google search API
- **[Pandas](https://pandas.pydata.org/)** - Powerful data manipulation and analysis library
- **[Click](https://click.palletsprojects.com/)** - Command-line interface creation toolkit
- **[Pydantic](https://pydantic-docs.helpmanual.io/)** - Data validation using Python type annotations

---

<div align="center">

**⭐ Star this repository if you find it helpful!**

[Report Bug](https://github.com/NgnPhamGiaHuy/google-cse-serp-extractor/issues) · [Request Feature](https://github.com/NgnPhamGiaHuy/google-cse-serp-extractor/issues) · [View Documentation](https://github.com/NgnPhamGiaHuy/google-cse-serp-extractor/wiki)

</div>