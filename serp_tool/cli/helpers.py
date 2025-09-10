import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from serp_tool.logging import cli_logger
from serp_tool.scraper import GoogleSerpScraper


def load_keywords(path: Path) -> List[str]:
    from serp_tool.handlers.readers import read_keywords_from_file
    return read_keywords_from_file(path)


def build_config_from_flags(SearchConfig, defaults, include_organic, include_paa, include_related, include_ads, include_ai_overview, selected_sites, allow_duplicates, max_pages, results_per_page):
    cfg_max_pages = max_pages if max_pages is not None else defaults.get('max_pages', 3)
    cfg_rpp = results_per_page if results_per_page is not None else defaults.get('results_per_page', 10)
    return SearchConfig(
        country_code=None,
        language_code=None,
        device=None,
        max_pages=cfg_max_pages,
        results_per_page=cfg_rpp,
        include_organic=include_organic,
        include_paa=include_paa,
        include_related=include_related,
        include_ads=include_ads,
        include_ai_overview=include_ai_overview,
        profile_sites=selected_sites,
        allow_duplicates=allow_duplicates
    )


def deduplicate_and_log(keywords: List[str], config, log_path: Path) -> Tuple[List[str], List[str]]:
    scraper_for_norm = GoogleSerpScraper()
    log_file = open(log_path, 'a', encoding='utf-8')
    row_id = 0
    unique_keywords: List[str] = []
    skipped_duplicates: List[str] = []
    seen_normalized = set() if not getattr(config, 'allow_duplicates', False) else None
    
    def create_log_entry(keyword: str, cleaned: str, normalized: str, is_duplicate: bool = False) -> dict:
        """Create a standardized log entry for a keyword."""
        return {
            'input_row_id': row_id,
            'original_input': str(keyword),
            'final_query': cleaned,
            'normalized_query_hash': scraper_for_norm.hash_normalized_query(normalized),
            'timestamp': datetime.utcnow().isoformat(),
            'deduplicated': is_duplicate
        }
    
    for k in keywords:
        row_id += 1
        if not k or not str(k).strip():
            continue
            
        cleaned, normalized = scraper_for_norm.compute_clean_and_normalized(k, config)
        
        if seen_normalized is not None:  # Deduplication enabled
            is_duplicate = normalized in seen_normalized
            if is_duplicate:
                skipped_duplicates.append(str(k))
            else:
                seen_normalized.add(normalized)
                unique_keywords.append(str(k))
            
            entry = create_log_entry(k, cleaned, normalized, is_duplicate)
        else:  # No deduplication
            unique_keywords.append(str(k))
            entry = create_log_entry(k, cleaned, normalized)
        
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    try:
        log_file.close()
    except Exception:
        pass
        
    if skipped_duplicates:
        cli_logger.info(
            f"Skipping {len(skipped_duplicates)} duplicate querie(s)",
            extra={"action": "dedup", "status": "skipped"}
        )
    return unique_keywords, skipped_duplicates


