import json
from pathlib import Path
from typing import Any, Dict, List, Union

import pandas as pd

from serp_tool.logging import files_logger
from serp_tool.handlers.flatteners import (
    _flatten_organic,
    _flatten_paa,
    _flatten_related,
    _flatten_paid,
    _flatten_ai_overview,
)


def export_results_to_json(results: List[Dict[str, Any]], file_path: Union[str, Path]) -> None:
    file_path = Path(file_path)
    rows = _flatten_organic(results)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)
    try:
        files_logger.info(
            f"Exported JSON rows: {len(rows)}",
            extra={"action": "export_json", "status": "success"}
        )
    except Exception:
        pass


def export_results_to_csv(results: List[Dict[str, Any]], file_path: Union[str, Path]) -> None:
    file_path = Path(file_path)
    organic_rows = _flatten_organic(results)
    df = pd.DataFrame(organic_rows)
    df.to_csv(file_path, index=False, encoding='utf-8-sig')
    try:
        files_logger.info(
            f"Exported CSV rows: {len(organic_rows)}",
            extra={"action": "export_csv", "status": "success"}
        )
    except Exception:
        pass


def export_results_to_excel(results: List[Dict[str, Any]], file_path: Union[str, Path]) -> None:
    file_path = Path(file_path)
    organic_rows = _flatten_organic(results)
    paa_rows = _flatten_paa(results)
    related_rows = _flatten_related(results)
    paid_rows = _flatten_paid(results)
    aio_rows = _flatten_ai_overview(results)

    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        pd.DataFrame(organic_rows).to_excel(writer, index=False, sheet_name='organic_results')
        if paa_rows:
            pd.DataFrame(paa_rows).to_excel(writer, index=False, sheet_name='people_also_ask')
        if related_rows:
            pd.DataFrame(related_rows).to_excel(writer, index=False, sheet_name='related_queries')
        if paid_rows:
            pd.DataFrame(paid_rows).to_excel(writer, index=False, sheet_name='paid_results')
        if aio_rows:
            pd.DataFrame(aio_rows).to_excel(writer, index=False, sheet_name='ai_overview')

        for sheet_name, ws in writer.sheets.items():
            for column in ws.columns:
                max_length = 0
                column_name = column[0].column_letter
                for cell in column:
                    try:
                        if cell.value is not None and len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except Exception:
                        pass
                adjusted_width = min(max_length + 2, 60)
                ws.column_dimensions[column_name].width = adjusted_width
    try:
        files_logger.info(
            f"Exported XLSX rows: {len(organic_rows)}",
            extra={"action": "export_xlsx", "status": "success"}
        )
    except Exception:
        pass


def export_results(results: List[Dict[str, Any]], file_path: Union[str, Path], format_type: str = None) -> None:
    file_path = Path(file_path)
    if format_type:
        format_type = format_type.lower()
    else:
        format_type = file_path.suffix.lower().lstrip('.')

    if format_type == 'json':
        export_results_to_json(results, file_path)
    elif format_type == 'csv':
        export_results_to_csv(results, file_path)
    elif format_type in ['xlsx', 'excel']:
        export_results_to_excel(results, file_path)
    else:
        raise ValueError(f"Unsupported export format: {format_type}")


