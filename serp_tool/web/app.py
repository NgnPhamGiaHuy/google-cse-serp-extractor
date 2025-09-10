from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import config
from serp_tool.logging import app_logger, setup_root_logging
from serp_tool.utils.temp_manager import get_temp_dir, cleanup_temp_dir
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_root_logging()
    # Initialize temp directory using temp_manager
    get_temp_dir()
    Path(config.io_settings.get("export_dir", "downloads")).mkdir(exist_ok=True)
    Path("templates").mkdir(exist_ok=True)
    try:
        config.validate_required()
        app_logger.info("Configuration validated", extra={"action": "config_validate", "status": "success"})
    except ValueError as e:
        app_logger.error(f"Configuration warning: {e}", extra={"action": "config_validate", "status": "fail"})
        app_logger.info("The application will start but scraping may not work without proper configuration.")
    try:
        yield
    finally:
        # Cleanup temp directory on shutdown
        cleanup_temp_dir()


app = FastAPI(title="Google SERP Scraping Tool", description="Bulk Google search result scraping using Google Custom Search Engine API", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(router)


