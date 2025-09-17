import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List

from models import SearchConfig
from serp_tool.clients.cse.client import QuotaExceededError
from serp_tool.logging import app_logger
from serp_tool.normalizer import normalize_items
from serp_tool.scraper import GoogleSerpScraper
from serp_tool.utils.temp_manager import get_inspections_dir
from .state import job_storage, results_storage


async def run_scraping_job(job_id: str, keywords: List[str], config: SearchConfig) -> None:
    """Run a background scraping job for a set of keywords.

    Updates in-memory job state throughout the lifecycle, logging important
    milestones and persisting inspection artifacts to disk.
    """
    try:
        job_storage[job_id].status = "running"
        job_storage[job_id].current_stage = "initializing"
        job_storage[job_id].last_updated = datetime.now()

        scraper = GoogleSerpScraper()
        app_logger.info(
            "Scraper initialized",
            extra={"action": "init_scraper", "status": "success", "query_id": job_id},
        )

        unique_keywords: List[str] = []
        skipped_duplicates: List[str] = []
        insp_dir = get_inspections_dir()
        log_path = insp_dir / "queries.log"
        log_file = open(log_path, "a", encoding="utf-8")
        row_id = 0

        if getattr(config, "allow_duplicates", False):
            for raw_keyword in keywords:
                row_id += 1
                if not raw_keyword or not str(raw_keyword).strip():
                    continue
                cleaned, normalized = scraper.compute_clean_and_normalized(raw_keyword, config)
                entry = {
                    "input_row_id": row_id,
                    "original_input": str(raw_keyword),
                    "final_query": cleaned,
                    "normalized_query_hash": scraper.hash_normalized_query(normalized),
                    "timestamp": datetime.utcnow().isoformat(),
                }
                log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")
                unique_keywords.append(str(raw_keyword))
        else:
            seen_normalized = set()
            for raw_keyword in keywords:
                row_id += 1
                if not raw_keyword or not str(raw_keyword).strip():
                    continue
                cleaned, normalized = scraper.compute_clean_and_normalized(raw_keyword, config)
                entry = {
                    "input_row_id": row_id,
                    "original_input": str(raw_keyword),
                    "final_query": cleaned,
                    "normalized_query_hash": scraper.hash_normalized_query(normalized),
                    "timestamp": datetime.utcnow().isoformat(),
                }
                if normalized in seen_normalized:
                    skipped_duplicates.append(str(raw_keyword))
                    entry["deduplicated"] = True
                else:
                    seen_normalized.add(normalized)
                    unique_keywords.append(str(raw_keyword))
                    entry["deduplicated"] = False
                log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")
        if skipped_duplicates:
            app_logger.info(
                f"Skipping {len(skipped_duplicates)} duplicate querie(s)",
                extra={"action": "dedup", "status": "skipped", "query_id": job_id},
            )

        all_results: List[Dict[str, Any]] = []
        completed = 0
        start_time = datetime.now()

        job_storage[job_id].current_stage = "processing"
        job_storage[job_id].last_updated = datetime.now()

        app_logger.info(
            f"Parsed {len(keywords)} keywords; {len(unique_keywords)} unique",
            extra={"action": "query_validation", "status": "success", "query_id": job_id},
        )

        for _, keyword in enumerate(unique_keywords):
            try:
                if not keyword or not str(keyword).strip():
                    app_logger.info(
                        "Skipping empty keyword row",
                        extra={"action": "skip_empty", "status": "skipped", "query_id": job_id},
                    )
                    continue

                job_storage[job_id].current_keyword = keyword
                job_storage[job_id].last_updated = datetime.now()

                if completed > 0:
                    elapsed_time_seconds = (datetime.now() - start_time).total_seconds()
                    processing_speed_per_min = (completed / elapsed_time_seconds) * 60
                    remaining_keywords = len(unique_keywords) - completed
                    estimated_remaining_seconds = (
                        int((remaining_keywords / processing_speed_per_min) * 60)
                        if processing_speed_per_min > 0
                        else None
                    )

                    job_storage[job_id].processing_speed = processing_speed_per_min
                    job_storage[job_id].estimated_time_remaining = estimated_remaining_seconds

                app_logger.info(
                    "Sending to Google CSE",
                    extra={
                        "action": "cse_request",
                        "status": "started",
                        "query_id": job_id,
                        "keyword": keyword,
                    },
                )

                safe_cfg = config
                try:
                    pages = int(getattr(config, "max_pages", 10) or 10)
                except Exception:
                    pages = 10
                if pages < 1:
                    safe_cfg = config.model_copy(update={"max_pages": 1})

                results = await scraper.scrape_keyword(keyword, safe_cfg)
                normalized = normalize_items(results)

                if hasattr(scraper, "_last_quota_error") and scraper._last_quota_error:
                    job_storage[job_id].quota_exceeded = True
                    job_storage[job_id].quota_error = {
                        "error_type": "quota_exceeded",
                        "message": str(scraper._last_quota_error),
                        "quota_info": scraper._last_quota_error.quota_info,
                        "help_links": scraper._last_quota_error.help_links,
                        "occurred_at": datetime.now().isoformat(),
                        "keyword": keyword,
                    }
                    app_logger.warning(
                        f"Quota exceeded during scraping of keyword '{keyword}'",
                        extra={
                            "action": "quota_exceeded",
                            "status": "warning",
                            "query_id": job_id,
                            "keyword": keyword,
                            "quota_info": scraper._last_quota_error.quota_info,
                        },
                    )
                    scraper._last_quota_error = None

                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    dump_path = insp_dir / f"{timestamp}_normalize_to_unified.json"
                    with open(dump_path, "w", encoding="utf-8") as f:
                        json.dump(normalized, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass

                all_results.extend(normalized)
                completed += 1
                job_storage[job_id].completed_keywords = completed
                job_storage[job_id].progress = int((completed / len(keywords)) * 100)
                job_storage[job_id].results_count = len(all_results)
                job_storage[job_id].last_updated = datetime.now()

                app_logger.info(
                    f"Received {len(results)} items; total {len(all_results)}",
                    extra={"action": "result_fetch", "status": "success", "query_id": job_id, "keyword": keyword},
                )
                await asyncio.sleep(1)
            except Exception as exc:
                app_logger.error(
                    f"Error scraping keyword '{keyword}': {str(exc)}",
                    extra={"action": "scrape", "status": "fail", "query_id": job_id, "keyword": keyword},
                )
                completed += 1
                job_storage[job_id].completed_keywords = completed
                job_storage[job_id].progress = int((completed / len(keywords)) * 100)
                job_storage[job_id].last_updated = datetime.now()

        job_storage[job_id].current_stage = "finalizing"
        job_storage[job_id].current_keyword = None
        job_storage[job_id].last_updated = datetime.now()

        results_storage[job_id] = all_results
        job_storage[job_id].status = "completed"
        job_storage[job_id].completed_at = datetime.now()
        job_storage[job_id].results_count = len(all_results)
        job_storage[job_id].current_stage = "completed"
        job_storage[job_id].last_updated = datetime.now()
        try:
            from serp_tool.handlers.flatteners import _flatten_organic
            organic_rows_count = len(_flatten_organic(all_results))
        except Exception:
            organic_rows_count = 0
        app_logger.info(
            f"Summary: sent={len(unique_keywords)} queries, cse_items={len(all_results)}, organic_rows={organic_rows_count}",
            extra={"action": "job_complete", "status": "success", "query_id": job_id},
        )
    except Exception as exc:
        job_storage[job_id].status = "failed"
        job_storage[job_id].error_message = str(exc)
        job_storage[job_id].completed_at = datetime.now()
        job_storage[job_id].current_stage = "failed"
        job_storage[job_id].last_updated = datetime.now()
        app_logger.error(
            f"Job failed: {str(exc)}", extra={"action": "job", "status": "fail", "query_id": job_id}
        )
    finally:
        try:
            log_file.close()
        except Exception:
            pass

