import json
import aiofiles
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

from fastapi import HTTPException

from serp_tool.logging import app_logger
from serp_tool.handlers.readers import read_keywords_from_file
from serp_tool.handlers.writers import export_results
from serp_tool.utils.temp_manager import get_temp_dir


DOWNLOADS_DIR = None  # set by app module based on config


async def save_upload_to_temp(file, temp_dir: Path = None) -> Path:
    """Save UploadFile to a temp directory and return the saved path."""
    if temp_dir is None:
        temp_dir = get_temp_dir()
    temp_dir.mkdir(exist_ok=True)
    suffix = Path(file.filename).suffix
    temp_path = temp_dir / f"{datetime.utcnow().timestamp()}_{file.filename}"
    async with aiofiles.open(temp_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    return temp_path


def parse_keywords_file(temp_file: Path) -> List[str]:
    """Parse keywords using existing readers; raise HTTPException on failure."""
    try:
        app_logger.info("Input file loaded", extra={"action": "input_load", "status": "success"})
        keywords = read_keywords_from_file(temp_file)
        app_logger.info("Query parsing completed", extra={"action": "query_parse", "status": "success"})
        return keywords
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing file: {str(e)}")


def perform_export(results: List[Dict[str, Any]], export_path: Path, fmt: str, job_id: str) -> None:
    """Export results using existing writers with logging and error mapping."""
    if fmt not in ['json', 'csv', 'xlsx']:
        raise HTTPException(status_code=400, detail="Invalid format. Use: json, csv, xlsx")
    try:
        app_logger.info("Export started", extra={"action": "export", "status": "started", "query_id": job_id})
        export_results(results, export_path, fmt)
        app_logger.info("Export completed", extra={"action": "export", "status": "success", "query_id": job_id})
    except Exception as e:
        app_logger.error(f"Export failed: {str(e)}", extra={"action": "export", "status": "fail", "query_id": job_id})
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


