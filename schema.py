"""
TypedDict schemas for Google SERP search results and data structures.

This module defines the type-safe data structures used throughout the application
for representing search queries, results, and unified search data.
"""

from typing import Any, Dict, List, Optional, TypedDict


class SearchQuery(TypedDict, total=False):
    """Schema for search query parameters.
    
    Attributes:
        term: The search query string (optional).
        page: The page number for pagination (optional, defaults to 1).
    """
    term: Optional[str]
    page: Optional[int]


class OrganicResult(TypedDict, total=False):
    """Schema for organic search results from search engines.
    
    Attributes:
        position: The position/rank of the result in search results.
        title: The title of the search result.
        url: The URL of the search result.
        displayedUrl: The display URL shown in search results.
        snippet: The snippet/description text of the result.
        siteLinks: Additional site links if available (e.g., sitelinks).
        metatags: Optional metadata tags extracted from the page.
        connectionsText: Text describing social connections/followers.
        connectionsCount: Number of social connections/followers.
    """
    position: Optional[int]
    title: Optional[str]
    url: Optional[str]
    displayedUrl: Optional[str]
    snippet: Optional[str]
    siteLinks: Optional[List[Dict[str, Any]]]
    # Optional enriched fields (if available from providers)
    metatags: Optional[Dict[str, Any]]
    connectionsText: Optional[str]
    connectionsCount: Optional[int]


class PeopleAlsoAskItem(TypedDict, total=False):
    """Schema for "People Also Ask" search result items.
    
    Attributes:
        question: The question text.
        answer: The answer text.
        url: Optional URL related to the question/answer.
    """
    question: Optional[str]
    answer: Optional[str]
    url: Optional[str]


class AdItem(TypedDict, total=False):
    """Schema for advertisement items in search results.
    
    Attributes:
        position: The position of the ad in search results.
        title: The ad title.
        url: The ad destination URL.
        advertiser: The name of the advertiser.
        snippet: The ad description/snippet text.
    """
    position: Optional[int]
    title: Optional[str]
    url: Optional[str]
    advertiser: Optional[str]
    snippet: Optional[str]


class UnifiedItem(TypedDict, total=False):
    """Unified schema for complete search result data.
    
    This combines all types of search results into a single structure
    that can represent data from different search providers.
    
    Attributes:
        searchQuery: The search query that generated these results.
        organicResults: List of organic search results.
        peopleAlsoAsk: Optional list of "People Also Ask" items.
        relatedSearches: Optional list of related search suggestions.
        ads: Optional list of advertisement items.
        aiOverview: Optional AI-generated overview content.
    """
    searchQuery: SearchQuery
    organicResults: List[OrganicResult]
    peopleAlsoAsk: Optional[List[PeopleAlsoAskItem]]
    relatedSearches: Optional[List[Any]]
    ads: Optional[List[AdItem]]
    aiOverview: Optional[Any]


def default_search_query() -> SearchQuery:
    """Create a default search query with standard values.
    
    Returns:
        SearchQuery: A search query with term=None and page=1.
    """
    return {
        "term": None,
        "page": 1,
    }


def empty_unified_item() -> UnifiedItem:
    """Create an empty unified search result item with default structure.
    
    Returns:
        UnifiedItem: An empty unified item with all lists initialized as empty
                    and optional fields set to None or appropriate defaults.
    """
    return {
        "searchQuery": default_search_query(),
        "organicResults": [],
        "peopleAlsoAsk": [],
        "relatedSearches": [],
        "ads": [],
        "aiOverview": None,
    }


