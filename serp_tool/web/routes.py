import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from config import config
from models import SearchConfig, SearchJobStatus, BulkSearchRequest
from serp_tool.logging import app_logger
from serp_tool.utils.token_manager import token_manager
from serp_tool.utils.platform_utils import (
    convert_platform_to_site_filter,
    validate_platform_name,
    get_platform_suggestions,
    process_platform_list
)
from .state import job_storage, results_storage
from .helpers import save_upload_to_temp, parse_keywords_file, perform_export
from .background import run_scraping_job


templates = Jinja2Templates(directory="templates")
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    app_logger.info("Serve home", extra={"action": "serve_home", "status": "success"})
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/api/upload-keywords")
async def upload_keywords(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    allowed_extensions = ['.json', '.csv', '.xlsx', '.xls']
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file format. Allowed: {', '.join(allowed_extensions)}")
    temp_file = await save_upload_to_temp(file)
    try:
        keywords = parse_keywords_file(temp_file)
        return {"success": True, "keywords": keywords, "count": len(keywords), "filename": file.filename}
    finally:
        try:
            temp_file.unlink()
        except Exception:
            pass


@router.post("/api/start-scraping")
async def start_scraping(background_tasks: BackgroundTasks, request: BulkSearchRequest):
    if not request.keywords:
        raise HTTPException(status_code=400, detail="No keywords provided")
    
    job_id = str(uuid.uuid4())
    job_status = SearchJobStatus(
        job_id=job_id,
        status="pending",
        progress=0,
        total_keywords=len(request.keywords),
        completed_keywords=0,
        created_at=datetime.now(),
    )
    job_storage[job_id] = job_status
    results_storage[job_id] = []
    background_tasks.add_task(run_scraping_job, job_id, request.keywords, request.config)
    app_logger.info("Job started", extra={"action": "job_start", "status": "success", "query_id": job_id, "keyword": "-"})
    return {"job_id": job_id, "status": "started"}


@router.get("/api/job-status/{job_id}")
async def get_job_status(job_id: str):
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_status = job_storage[job_id]
    
    # Include quota error information in response
    response_data = job_status.model_dump()
    
    # If quota was exceeded, add user-friendly error information
    if job_status.quota_exceeded and job_status.quota_error:
        response_data["quota_error_display"] = {
            "status": "error",
            "error_type": "quota_exceeded",
            "message": "Google CSE daily query limit has been reached. Please try again tomorrow or use a new API key.",
            "quota_limit": job_status.quota_error.get("quota_info", {}).get("quota_limit_value"),
            "quota_metric": job_status.quota_error.get("quota_info", {}).get("quota_metric"),
            "help_links": job_status.quota_error.get("help_links", []),
            "occurred_at": job_status.quota_error.get("occurred_at"),
            "affected_keyword": job_status.quota_error.get("keyword")
        }
    
    return response_data


@router.get("/api/job-results/{job_id}")
async def get_job_results(job_id: str, limit: Optional[int] = None):
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    if job_storage[job_id].status != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    results = results_storage.get(job_id, [])
    if limit:
        results = results[:limit]
    return {"job_id": job_id, "total_results": len(results_storage.get(job_id, [])), "returned_results": len(results), "results": results}


@router.post("/api/export-results/{job_id}")
async def export_job_results(job_id: str, format: str = Form(...)):
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    if job_storage[job_id].status != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    results = results_storage.get(job_id, [])
    if not results:
        raise HTTPException(status_code=400, detail="No results to export")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pattern = config.io_settings.get("filename_pattern", "search_results_{job}_{timestamp}")
    filename = f"{pattern.format(job=job_id[:8], timestamp=timestamp)}.{format}"
    export_dir = Path(config.io_settings.get("export_dir", "downloads"))
    export_dir.mkdir(exist_ok=True)
    export_path = export_dir / filename
    perform_export(results, export_path, format, job_id)
    return {"success": True, "filename": filename, "download_url": f"/api/download/{filename}"}


@router.get("/api/download/{filename}")
async def download_file(filename: str):
    file_path = Path(config.io_settings.get("export_dir", "downloads")) / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=file_path, filename=filename, media_type='application/octet-stream')


@router.delete("/api/job/{job_id}")
async def delete_job(job_id: str):
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    del job_storage[job_id]
    if job_id in results_storage:
        del results_storage[job_id]
    app_logger.info("Job deleted", extra={"action": "job_delete", "status": "success", "query_id": job_id})
    return {"success": True, "message": "Job deleted"}


@router.get("/api/jobs")
async def list_jobs():
    jobs: List[Dict[str, Any]] = []
    for job_id, job_status in job_storage.items():
        jobs.append({
            "job_id": job_id,
            "status": job_status.status,
            "progress": job_status.progress,
            "total_keywords": job_status.total_keywords,
            "completed_keywords": job_status.completed_keywords,
            "results_count": job_status.results_count,
            "created_at": job_status.created_at.isoformat(),
            "completed_at": job_status.completed_at.isoformat() if job_status.completed_at else None
        })
    return {"jobs": jobs}


# Token management endpoints
@router.get("/api/token-status")
async def get_token_status():
    """Get the current status of all API tokens."""
    try:
        status = token_manager.get_token_status()
        return {"success": True, "status": status}
    except Exception as e:
        app_logger.error(f"Failed to get token status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get token status")


@router.post("/api/validate-token")
async def validate_token(token_type: str = Form(...), token_value: str = Form(...)):
    """Validate an API token."""
    try:
        is_valid, message = token_manager.validate_token_with_api(token_type, token_value)
        return {"success": True, "valid": is_valid, "message": message}
    except Exception as e:
        app_logger.error(f"Token validation failed: {e}")
        return {"success": False, "valid": False, "message": f"Validation error: {str(e)}"}


@router.post("/api/set-token")
async def set_token(token_type: str = Form(...), token_value: str = Form(...)):
    """Set an API token in temporary storage."""
    try:
        success, message = token_manager.set_token(token_type, token_value)
        if success:
            app_logger.info(f"API token saved: {token_type}", extra={
                "action": "api_key_save", 
                "status": "success",
                "token_type": token_type,
                "reason": "quota_exceeded_recovery"
            })
        return {"success": success, "message": message}
    except Exception as e:
        app_logger.error(f"Failed to set token: {e}")
        raise HTTPException(status_code=500, detail="Failed to set token")


@router.delete("/api/clear-tokens")
async def clear_tokens():
    """Clear all tokens from temporary storage."""
    try:
        token_manager.clear_all_tokens()
        app_logger.info("API keys cleared by user action", extra={
            "action": "api_key_change", 
            "status": "success",
            "reason": "quota_exceeded_recovery"
        })
        return {"success": True, "message": "All tokens cleared"}
    except Exception as e:
        app_logger.error(f"Failed to clear tokens: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear tokens")


# Backup token management endpoints
@router.post("/api/set-backup-token")
async def set_backup_token(token_type: str = Form(...), token_value: str = Form(...)):
    """Set a backup API token for automatic switching when quota is exceeded."""
    try:
        success, message = token_manager.set_backup_token(token_type, token_value)
        return {"success": success, "message": message}
    except Exception as e:
        app_logger.error(f"Failed to set backup token: {e}")
        raise HTTPException(status_code=500, detail="Failed to set backup token")


@router.get("/api/backup-token-status")
async def get_backup_token_status():
    """Get the current status of all backup API tokens."""
    try:
        status = token_manager.get_backup_token_status()
        return {"success": True, "status": status}
    except Exception as e:
        app_logger.error(f"Failed to get backup token status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get backup token status")


@router.post("/api/switch-to-backup")
async def switch_to_backup_token(token_type: str = Form(...)):
    """Manually switch to backup token for a specific type."""
    try:
        success, message = token_manager.switch_to_backup_token(token_type)
        return {"success": success, "message": message}
    except Exception as e:
        app_logger.error(f"Failed to switch to backup token: {e}")
        raise HTTPException(status_code=500, detail="Failed to switch to backup token")


@router.delete("/api/clear-backup-tokens")
async def clear_backup_tokens():
    """Clear all backup tokens from temporary storage."""
    try:
        token_manager.clear_backup_tokens()
        return {"success": True, "message": "All backup tokens cleared"}
    except Exception as e:
        app_logger.error(f"Failed to clear backup tokens: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear backup tokens")


# Platform management endpoints
@router.get("/api/platform-suggestions")
async def get_platform_suggestions_endpoint(query: str = "", limit: int = 10):
    """Get platform suggestions based on query."""
    try:
        suggestions = get_platform_suggestions(query, limit)
        return {"success": True, "suggestions": suggestions}
    except Exception as e:
        app_logger.error(f"Failed to get platform suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get platform suggestions")


@router.post("/api/validate-platform")
async def validate_platform_endpoint(platform_name: str = Form(...)):
    """Validate a platform name."""
    try:
        validation_result = validate_platform_name(platform_name)
        return {"success": True, **validation_result}
    except Exception as e:
        app_logger.error(f"Failed to validate platform: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate platform")


@router.post("/api/convert-platform")
async def convert_platform_endpoint(platform_name: str = Form(...)):
    """Convert platform name to site filter."""
    try:
        site_filter = convert_platform_to_site_filter(platform_name)
        return {"success": True, "site_filter": site_filter}
    except Exception as e:
        app_logger.error(f"Failed to convert platform: {e}")
        raise HTTPException(status_code=500, detail="Failed to convert platform")


@router.post("/api/process-platforms")
async def process_platforms_endpoint(platform_names: List[str] = Form(...)):
    """Process a list of platform names to site filters."""
    try:
        site_filters = process_platform_list(platform_names)
        return {"success": True, "site_filters": site_filters}
    except Exception as e:
        app_logger.error(f"Failed to process platforms: {e}")
        raise HTTPException(status_code=500, detail="Failed to process platforms")


