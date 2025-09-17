import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
from fastapi import HTTPException

from serp_tool.handlers.readers import read_keywords_from_file
from serp_tool.handlers.writers import export_results
from serp_tool.logging import app_logger
from serp_tool.utils.temp_manager import get_temp_dir


async def save_upload_to_temp(file, temp_dir: Optional[Path] = None) -> Path:
    """Persist an uploaded file to a temporary directory.

    Args:
        file: Starlette/FastAPI UploadFile-like object exposing .filename and .read().
        temp_dir: Optional temp directory. When None, resolves via get_temp_dir().

    Returns:
        Path to the written temporary file.
    """
    if temp_dir is None:
        temp_dir = get_temp_dir()
    temp_dir.mkdir(exist_ok=True)
    temp_path = temp_dir / f"{datetime.utcnow().timestamp()}_{file.filename}"
    async with aiofiles.open(temp_path, "wb") as buffer:
        content = await file.read()
        await buffer.write(content)
    return temp_path


def parse_keywords_file(temp_file: Path) -> List[str]:
    """Parse keywords from a previously saved upload file.

    Logs progress and translates parsing errors into HTTP 400 errors.

    Args:
        temp_file: Path to the uploaded temporary file.

    Returns:
        List of keyword strings.
    """
    try:
        app_logger.info("Input file loaded", extra={"action": "input_load", "status": "success"})
        keywords = read_keywords_from_file(temp_file)
        app_logger.info("Query parsing completed", extra={"action": "query_parse", "status": "success"})
        return keywords
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Error parsing file: {str(exc)}")


def perform_export(results: List[Dict[str, Any]], export_path: Path, fmt: str, job_id: str) -> None:
    """Export results to the given path in the specified format.

    Args:
        results: List of result item dictionaries.
        export_path: Destination path for the exported file.
        fmt: One of 'json', 'csv', or 'xlsx'.
        job_id: Related job identifier for logging context.
    """
    if fmt not in ["json", "csv", "xlsx"]:
        raise HTTPException(status_code=400, detail="Invalid format. Use: json, csv, xlsx")
    try:
        app_logger.info("Export started", extra={"action": "export", "status": "started", "query_id": job_id})
        export_results(results, export_path, fmt)
        app_logger.info("Export completed", extra={"action": "export", "status": "success", "query_id": job_id})
    except Exception as exc:
        app_logger.error(
            f"Export failed: {str(exc)}",
            extra={"action": "export", "status": "fail", "query_id": job_id},
        )
        raise HTTPException(status_code=500, detail=f"Export failed: {str(exc)}")

