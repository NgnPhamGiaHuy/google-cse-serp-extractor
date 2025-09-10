import json
from pathlib import Path
from typing import List, Tuple, Union

import pandas as pd

from serp_tool.handlers.common import _compose_query


def _read_keywords_from_json(file_path: Path) -> List[str]:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    override_keys = {
        'uule', 'results_per_page', 'max_pages'
    }

    if isinstance(data, list):
        merged: List[str] = []
        for item in data:
            if isinstance(item, dict):
                non_override_items: List[Tuple[str, str]] = []
                for k, v in item.items():
                    if str(k).strip().lower() in override_keys:
                        continue
                    if v is None:
                        continue
                    s = str(v).strip()
                    if s:
                        non_override_items.append((str(k), s))
                if non_override_items:
                    anchor_val = non_override_items[0][1]
                    role_vals = [val for _, val in non_override_items[1:]]
                    merged.append(_compose_query(anchor_val, role_vals, None))
            else:
                s = str(item).strip()
                if s:
                    merged.append(_compose_query(s, [], None))
        return merged
    elif isinstance(data, dict):
        for key in ['keywords', 'queries', 'terms', 'data']:
            if key in data and isinstance(data[key], list):
                normalized: List[str] = []
                for item in data[key]:
                    if isinstance(item, dict):
                        non_override_items: List[Tuple[str, str]] = []
                        for k, v in item.items():
                            if str(k).strip().lower() in override_keys:
                                continue
                            if v is None:
                                continue
                            s = str(v).strip()
                            if s:
                                non_override_items.append((str(k), s))
                        if non_override_items:
                            anchor_val = non_override_items[0][1]
                            role_vals = [val for _, val in non_override_items[1:]]
                            normalized.append(_compose_query(anchor_val, role_vals, None))
                    else:
                        s = str(item).strip()
                        if s:
                            normalized.append(_compose_query(s, [], None))
                return normalized

        keywords = []
        for value in data.values():
            if isinstance(value, list):
                for item in value:
                    s = str(item).strip()
                    if s:
                        keywords.append(_compose_query(s, [], None))
            elif isinstance(value, str):
                s = value.strip()
                if s:
                    keywords.append(_compose_query(s, [], None))
        return keywords

    raise ValueError("Invalid JSON structure. Expected list of keywords or object with keyword arrays.")


def _read_keywords_from_csv(file_path: Path) -> List[str]:
    try:
        df = pd.read_csv(file_path)

        override_cols = {
            'uule', 'results_per_page', 'max_pages'
        }

        query_col = None
        for col in df.columns:
            if str(col).strip().lower() in ['query', 'queries']:
                query_col = col
                break
        if query_col is not None:
            queries = df[query_col].dropna().astype(str).map(str.strip).tolist()
            return [q for q in queries if q]

        merge_columns: List[str] = []
        for col in df.columns:
            if str(col).strip().lower() in override_cols:
                continue
            merge_columns.append(col)

        if not merge_columns:
            return []

        merged_queries: List[str] = []
        for _, row in df.iterrows():
            anchor_val = None
            role_vals: List[str] = []
            for idx, col in enumerate(merge_columns):
                val = row.get(col)
                if pd.isna(val):
                    continue
                s = str(val).strip()
                if not s:
                    continue
                if anchor_val is None:
                    anchor_val = s
                else:
                    role_vals.append(s)
            if anchor_val:
                merged_queries.append(_compose_query(anchor_val, role_vals, None))

        return merged_queries

    except Exception as e:
        raise ValueError(f"Error reading CSV file: {str(e)}")


def _read_keywords_from_excel(file_path: Path) -> List[str]:
    try:
        df = pd.read_excel(file_path, engine='openpyxl')

        override_cols = {
            'uule', 'results_per_page', 'max_pages'
        }

        query_col = None
        for col in df.columns:
            if str(col).strip().lower() in ['query', 'queries']:
                query_col = col
                break
        if query_col is not None:
            queries = df[query_col].dropna().astype(str).map(str.strip).tolist()
            return [q for q in queries if q]

        merge_columns: List[str] = []
        for col in df.columns:
            if str(col).strip().lower() in override_cols:
                continue
            merge_columns.append(col)

        if not merge_columns:
            return []

        merged_queries: List[str] = []
        for _, row in df.iterrows():
            anchor_val = None
            role_vals: List[str] = []
            for idx, col in enumerate(merge_columns):
                val = row.get(col)
                if pd.isna(val):
                    continue
                s = str(val).strip()
                if not s:
                    continue
                if anchor_val is None:
                    anchor_val = s
                else:
                    role_vals.append(s)
            if anchor_val:
                merged_queries.append(_compose_query(anchor_val, role_vals, None))

        return merged_queries

    except Exception as e:
        raise ValueError(f"Error reading Excel file: {str(e)}")


def read_keywords_from_file(file_path: Union[str, Path]) -> List[str]:
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    file_extension = file_path.suffix.lower()
    if file_extension == '.json':
        return _read_keywords_from_json(file_path)
    elif file_extension == '.csv':
        return _read_keywords_from_csv(file_path)
    elif file_extension in ['.xlsx', '.xls']:
        return _read_keywords_from_excel(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")


