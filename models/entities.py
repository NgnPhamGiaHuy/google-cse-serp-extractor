from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from .search_config import SearchConfig


class SearchResult(BaseModel):
    """Individual search result"""
    keyword: str
    position: int
    page: int
    type: str  # 'organic', 'paa', 'related', 'ads', 'aiOverview'
    title: str
    url: str
    snippet: Optional[str] = None
    domain: str
    retrieved_at: datetime


class BulkSearchRequest(BaseModel):
    """Request for bulk search operation"""
    keywords: List[str]
    config: SearchConfig


