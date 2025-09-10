from typing import Optional, List
from pydantic import BaseModel, Field


class SearchConfig(BaseModel):
    """Configuration for Google search scraping"""
    max_pages: int = Field(default=3, ge=1, le=10, description="Maximum pages to scrape (default 3)")
    results_per_page: int = Field(default=10, ge=1, le=100, description="Results per page")
    include_organic: bool = Field(default=True, description="Include organic results")
    include_paa: bool = Field(default=False, description="Include People Also Ask")
    include_related: bool = Field(default=False, description="Include related searches")
    include_ads: bool = Field(default=False, description="Include ads")
    include_ai_overview: bool = Field(default=False, description="Include AI overview")
    profile_sites: Optional[List[str]] = Field(default=None, description="List of site: filters to target human profiles")
    allow_duplicates: bool = Field(default=False, description="Allow duplicate queries after normalization")
    split_long_queries: bool = Field(default=False, description="Split overly long queries into multiple sub-queries")


