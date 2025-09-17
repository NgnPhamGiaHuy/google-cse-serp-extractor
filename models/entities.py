from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List

from .search_config import SearchConfig


class SearchResult(BaseModel):
    """Represents a single search result item."""

    keyword: str
    position: int
    page: int
    type: str
    title: str
    url: str
    snippet: Optional[str] = None
    domain: str
    retrieved_at: datetime


class BulkSearchRequest(BaseModel):
    """Request schema for bulk search operations."""

    keywords: List[str]
    config: SearchConfig


