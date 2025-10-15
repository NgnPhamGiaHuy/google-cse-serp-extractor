# Google CSE SERP Extractor – Bulk Google results to clean files

![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-API%20server-009688)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

## 📝 Description

Modern research, lead generation, and SEO analysis often start with the same repetitive chore: opening Google, running the same queries, copying results, and pasting into spreadsheets. It’s slow, error‑prone, and hard to repeat.

Google CSE SERP Extractor turns that into a reliable, repeatable workflow. It uses the official Google Custom Search JSON API (CSE) to fetch results in bulk, normalizes them into a unified structure, and exports clean JSON/CSV/XLSX files. Use the web UI to upload a file and track jobs visually, or the CLI for automation. Built‑in caching and a daily usage tracker help avoid quota surprises.

This project benefits analysts, growth/ops teams, data engineers, and researchers who need bulk SERP data with minimal overhead and audit‑friendly logs.

## ✨ Features

-   **Run bulk searches (Web + CLI)**: Upload keyword files in the web app or run from the command line. Reduces typical manual effort of copy/pasting results across dozens of queries.
-   **Official Google CSE client with caching**: Uses `https://www.googleapis.com/customsearch/v1`. Caches responses on disk and counts only real HTTP calls to conserve daily quota.
-   **Unified data model and normalizers**: Converts raw provider responses into a stable unified schema (organic, PAA, related, ads, AI overview placeholders). Saves time when feeding downstream analysis.
-   **Smart de‑duplication**: Normalizes queries and prevents redundant calls unless explicitly allowed. Reduces repeated API use and result noise.
-   **Configurable exports**: Writes JSON, CSV, and Excel with auto‑sized columns. Eliminates manual spreadsheet cleanup.
-   **Usage tracking and quota‑aware UX**: Daily counter with graceful errors and recovery paths. Prevents failed runs late in the day.
-   **Backup token support**: Switches to backup Google API key if the primary hits quota. Minimizes downtime.
-   **FastAPI web interface**: Upload keywords, start jobs, monitor progress, and download results directly.
-   **Typed models and structured logs**: Pydantic schemas and contextual logs for easier debugging and auditing.

## ⚙️ Installation

The repository provides two supported setup paths. Choose one that matches your environment.

### Option A — macOS one‑shot installer

A guided installer provisions a virtual environment, installs dependencies, and prepares `.env`.

```bash
# From the project root
chmod +x setup.sh
./setup.sh
```

Notes:

-   The installer targets macOS (`$OSTYPE` check). It creates `venv/`, installs from `requirements.txt`, and copies `env.example` to `.env`.
-   During setup you can enter `GOOGLE_API_KEY` and `GOOGLE_CSE_CX` interactively (or edit `.env` later).

### Option B — Manual setup (any OS)

```bash
# From the project root
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

# Copy env template and edit values
envfile=.env
[ -f "$envfile" ] || cp env.example "$envfile"
# then open .env and set GOOGLE_API_KEY and GOOGLE_CSE_CX
```

### Start the web server

```bash
# With helper script (activates venv and validates prerequisites)
chmod +x run.sh
./run.sh             # defaults to http://localhost:8000
# or choose a port
./run.sh 8080
```

If `app.py --port` is unsupported, the launcher falls back to:

```bash
uvicorn serp_tool.web.app:app --host 0.0.0.0 --port 8000 --reload
```

### Command‑line interface

Use the Click‑based CLI to run scraping and check usage. You can invoke via the Python entry or the wrapper script.

```bash
# Activate the environment first
source venv/bin/activate

# Show command groups and options
python cli.py --help

# Run a scrape job (JSON, CSV, or Excel input)
python cli.py scrape \
  --keywords keywords.xlsx \
  --output downloads/results.xlsx \
  --max-pages 5 \
  --include-organic \
  --no-paa --no-related --no-ads --no-ai-overview

# Check today's usage according to the internal tracker
python cli.py usage
```

Wrapper launcher (also works; pass the subcommand):

```bash
chmod +x cli.sh
./cli.sh scrape --keywords keywords.csv --output results.csv --max-pages 2
```

## 🚀 Usage

Below are realistic task flows showing how the tool reduces manual steps.

### Before vs After examples

1. Bulk research (dozens of Google queries)

-   Before: Manually search each query, paginate, copy titles/URLs into a spreadsheet.
-   After:
    ```bash
    source venv/bin/activate
    python cli.py scrape --keywords input.xlsx --output downloads/research.xlsx --max-pages 3
    ```
    Result: Clean XLSX with normalized columns and auto widths.

2. Lightweight daily monitoring with web UI

-   Before: Re‑running ad‑hoc searches and reformatting outputs every day.
-   After:
    -   Start: `./run.sh` → open `http://localhost:8000`
    -   Upload: Select `input.csv` (or `.xlsx`, `.json`)
    -   Run: Start job, watch progress, and download the finished file from the browser.

3. Quota‑safe runs

-   Before: Jobs fail mid‑run when API limits are reached, wasting time.
-   After:
    ```bash
    python cli.py usage  # shows used/quota for today
    ```
    The client caches responses and only counts real HTTP calls; if the Google CSE quota is exceeded, the app can switch to a backup API key when configured.

### Web API endpoints (selection)

-   `GET /` – Serve web UI
-   `POST /api/upload-keywords` – Validate and preview uploaded keywords
-   `POST /api/start-scraping` – Start a background job
-   `GET /api/job-status/{job_id}` – Poll job progress and quota info
-   `GET /api/job-results/{job_id}` – Retrieve normalized results
-   `POST /api/export-results/{job_id}` – Persist results to disk and return a download URL
-   `GET /api/download/{filename}` – Download exported files
-   Token and platform helpers under `/api/*token*` and `/api/*platform*`

## 🔧 Configuration

Configuration is loaded from environment variables, `.env`, and `config.yaml` (env wins). See `env.example` for guided values.

Environment variables (from `env.example`):

```bash
GOOGLE_API_KEY=        # Primary API key (Custom Search JSON API)
GOOGLE_CSE_CX=         # Primary Programmable Search Engine ID (CX)
GOOGLE_API_KEY_BACKUP= # Optional backup API key
GOOGLE_CX_BACKUP=      # Optional backup CX (paired with backup key)
DEBUG=false            # Optional: enable debug logging
LOG_LEVEL=INFO         # Optional: DEBUG|INFO|WARNING|ERROR|CRITICAL
APPLY_LOCALE_HINTS=false
MAX_CONCURRENT_JOBS=5
REQUEST_TIMEOUT=300
CACHE_TTL_SECONDS=86400
```

Key `config.yaml` sections (defaults):

-   `api.google.base_url`: `https://www.googleapis.com/customsearch/v1`
-   `search`: `results_per_page=10`, `max_pages=10`
-   `io`: `export_dir=downloads`, `filename_pattern=search_results_{job}_{timestamp}`
-   `caching.ttl_seconds`: `86400` (24h)
-   `usage.daily_quota`: `100`

Notes:

-   The app validates `GOOGLE_API_KEY` and `GOOGLE_CSE_CX` at startup for scraping.
-   Locale hints (`lr/gl`) are applied when enabled and language/country are supplied.

## 🗂️ Folder structure

```text
.
├── app.py                         # Dev runner (starts uvicorn: serp_tool.web.app)
├── cli.py                         # CLI entry (Click group: scrape, usage)
├── cli.sh                         # CLI launcher (requires subcommand)
├── run.sh                         # Web server launcher (port detection, reload)
├── setup.sh                       # macOS installer (venv + deps + .env)
├── config/
│   ├── core.py                    # Config loader (env + YAML merge)
│   └── __init__.py
├── config.yaml                    # Runtime defaults (non‑secret)
├── env.example                    # Template for .env
├── models/                        # Pydantic models (requests, config, job status)
│   ├── entities.py
│   ├── job_status.py
│   └── search_config.py
├── serp_tool/
│   ├── cli/                       # Click CLI (commands + helpers)
│   │   ├── main.py
│   │   └── helpers.py
│   ├── clients/
│   │   └── cse/                   # Google CSE client, cache, mapping, HTTP
│   ├── handlers/                  # Readers, writers, flatteners
│   ├── logging/                   # Structured logging utilities
│   ├── normalizer/                # Unified schema normalization
│   ├── scraper/                   # Scraper orchestration (GoogleSerpScraper)
│   ├── utils/                     # Quota, tokens, temp/cache, delays, platform
│   └── web/                       # FastAPI app, routes, background jobs, state
├── static/                        # CSS/JS assets for web UI
├── templates/                     # Jinja2 templates (index, base)
├── downloads/                     # Exported files
├── state/                         # Usage tracker JSON
├── requirements.txt               # Runtime dependencies
└── LICENSE                        # MIT
```

## 🤝 Contributing

Contributions are welcome. A typical flow:

-   Fork and clone the repository.
-   Create a feature branch: `git checkout -b feat/your-feature`.
-   Install with `./setup.sh` (macOS) or manual steps above, and validate `python cli.py --help`.
-   Make focused edits with clear commit messages.
-   Run the app (`./run.sh`) and/or CLI to verify changes locally.
-   Open a pull request against `main` with a concise description and screenshots/logs if relevant.

## 📄 License

This project is licensed under the MIT License. See `LICENSE` for details.

## 👤 Author

| Name          | GitHub                                             | LinkedIn                                                             |
| ------------- | -------------------------------------------------- | -------------------------------------------------------------------- |
| NgnPhamGiaHuy | [@NgnPhamGiaHuy](https://github.com/NgnPhamGiaHuy) | [Nguyen Pham Gia Huy](https://www.linkedin.com/in/nguyenphamgiahuy/) |

## 🙏 Acknowledgements

-   Google Custom Search JSON API for reliable access to search results
-   FastAPI, Pydantic, Click, Pandas, and OpenPyXL for the surrounding ecosystem
-   All open‑source contributors who inspire practical, reliable tooling
