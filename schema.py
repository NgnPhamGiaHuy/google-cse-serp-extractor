
from typing import Any, Dict, List, Optional, TypedDict


class SearchQuery(TypedDict, total=False):
    term: Optional[str]
    page: Optional[int]


class OrganicResult(TypedDict, total=False):
    position: Optional[int]
    title: Optional[str]
    url: Optional[str]
    displayedUrl: Optional[str]
    snippet: Optional[str]
    siteLinks: Optional[List[Dict[str, Any]]]

    metatags: Optional[Dict[str, Any]]
    connectionsText: Optional[str]
    connectionsCount: Optional[int]


class PeopleAlsoAskItem(TypedDict, total=False):
    question: Optional[str]
    answer: Optional[str]
    url: Optional[str]


class AdItem(TypedDict, total=False):
    position: Optional[int]
    title: Optional[str]
    url: Optional[str]
    advertiser: Optional[str]
    snippet: Optional[str]


class UnifiedItem(TypedDict, total=False):
    searchQuery: SearchQuery
    organicResults: List[OrganicResult]
    peopleAlsoAsk: Optional[List[PeopleAlsoAskItem]]
    relatedSearches: Optional[List[Any]]
    ads: Optional[List[AdItem]]
    aiOverview: Optional[Any]


def default_search_query() -> SearchQuery:
    return {
        "term": None,
        "page": 1,
    }


def empty_unified_item() -> UnifiedItem:
    return {
        "searchQuery": default_search_query(),
        "organicResults": [],
        "peopleAlsoAsk": [],
        "relatedSearches": [],
        "ads": [],
        "aiOverview": None,
    }


