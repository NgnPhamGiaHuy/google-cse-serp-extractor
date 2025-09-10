"""
Platform utilities for converting platform names to Google site: filters
"""
import re
from typing import List, Optional, Dict, Any


# Popular platform mappings
PLATFORM_MAPPINGS = {
    # Social & Professional Networks
    'linkedin': 'site:linkedin.com/in',
    'linkedin vietnam': 'site:vn.linkedin.com/in',
    'facebook': 'site:facebook.com',
    'twitter': 'site:twitter.com',
    'instagram': 'site:instagram.com',
    'tiktok': 'site:tiktok.com',
    'snapchat': 'site:snapchat.com',
    'pinterest': 'site:pinterest.com',
    'tumblr': 'site:tumblr.com',
    'discord': 'site:discord.com',
    'telegram': 'site:t.me',
    'whatsapp': 'site:wa.me',
    
    # Developer & Tech Platforms
    'github': 'site:github.com',
    'stack overflow': 'site:stackoverflow.com',
    'dev.to': 'site:dev.to',
    'hackernews': 'site:news.ycombinator.com',
    'reddit': 'site:reddit.com',
    
    # Content & Media
    'youtube': 'site:youtube.com',
    'vimeo': 'site:vimeo.com',
    'twitch': 'site:twitch.tv',
    'medium': 'site:medium.com',
    'flickr': 'site:flickr.com',
    
    # Design & Creative
    'behance': 'site:behance.net',
    'dribbble': 'site:dribbble.com',
    
    # Business & Funding
    'crunchbase': 'site:crunchbase.com',
    'angellist': 'site:angel.co',
    'producthunt': 'site:producthunt.com',
    'kickstarter': 'site:kickstarter.com',
    'indiegogo': 'site:indiegogo.com',
    'patreon': 'site:patreon.com',
    
    # Q&A & Knowledge
    'quora': 'site:quora.com',
    'slideshare': 'site:slideshare.net',
    'scribd': 'site:scribd.com',
    'issuu': 'site:issuu.com',
    
    # Academic & Research
    'academia': 'site:academia.edu',
    'researchgate': 'site:researchgate.net',
    'orcid': 'site:orcid.org',
    'scholar': 'site:scholar.google.com',
    'arxiv': 'site:arxiv.org',
    'pubmed': 'site:pubmed.ncbi.nlm.nih.gov',
    
    # Academic Publishers
    'ieee': 'site:ieee.org',
    'acm': 'site:dl.acm.org',
    'springer': 'site:link.springer.com',
    'elsevier': 'site:sciencedirect.com',
    'wiley': 'site:onlinelibrary.wiley.com',
    'nature': 'site:nature.com',
    'science': 'site:science.org',
    'cell': 'site:cell.com',
    'plos': 'site:journals.plos.org',
    'bmc': 'site:bmc.com',
    'frontiers': 'site:frontiersin.org',
    'mdpi': 'site:mdpi.com',
    'hindawi': 'site:hindawi.com',
    'cogent': 'site:cogentoa.com',
    'sage': 'site:journals.sagepub.com',
    'taylor': 'site:tandfonline.com',
    'emerald': 'site:emerald.com'
}


def normalize_platform_name(platform_name: str) -> str:
    """
    Normalize platform name for consistent matching
    
    Args:
        platform_name: Raw platform name input
        
    Returns:
        Normalized platform name
    """
    if not platform_name:
        return ""
    
    # Convert to lowercase and strip whitespace
    normalized = platform_name.lower().strip()
    
    # Remove common prefixes
    prefixes_to_remove = ['www.', 'http://', 'https://', 'site:']
    for prefix in prefixes_to_remove:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):]
    
    # Remove trailing slashes and common paths
    normalized = re.sub(r'/+$', '', normalized)
    normalized = re.sub(r'/(in|profile|user|u)/?$', '', normalized)
    
    return normalized


def convert_platform_to_site_filter(platform_name: str) -> str:
    """
    Convert platform name to Google site: filter
    
    Args:
        platform_name: Platform name (e.g., 'LinkedIn', 'GitHub', 'github.com')
        
    Returns:
        Google site: filter (e.g., 'site:linkedin.com/in')
    """
    if not platform_name:
        return ""
    
    # Check if already a site: filter
    if platform_name.lower().startswith('site:'):
        return platform_name
    
    normalized = normalize_platform_name(platform_name)
    
    # Check direct mappings first
    if normalized in PLATFORM_MAPPINGS:
        return PLATFORM_MAPPINGS[normalized]
    
    # Check partial matches
    for key, value in PLATFORM_MAPPINGS.items():
        if normalized in key or key in normalized:
            return value
    
    # Auto-convert based on domain patterns
    if '.' in normalized and not normalized.startswith('site:'):
        # It looks like a domain
        domain = normalized
        
        # Handle common profile paths
        if 'linkedin' in domain and not domain.endswith('/in'):
            if not domain.endswith('/'):
                domain += '/'
            domain += 'in'
        
        return f"site:{domain}"
    
    # If no domain detected, assume .com
    if not '.' in normalized and not ' ' in normalized:
        return f"site:{normalized}.com"
    
    # Fallback: treat as-is with site: prefix
    return f"site:{normalized}"


def validate_platform_name(platform_name: str) -> Dict[str, Any]:
    """
    Validate platform name input
    
    Args:
        platform_name: Platform name to validate
        
    Returns:
        Dictionary with 'valid' boolean and 'error' message if invalid
    """
    if not platform_name or not platform_name.strip():
        return {"valid": False, "error": "Platform name cannot be empty"}
    
    normalized = normalize_platform_name(platform_name)
    
    # Check for invalid characters
    if not re.match(r'^[a-zA-Z0-9\s\.\-_\/]+$', normalized):
        return {"valid": False, "error": "Platform name contains invalid characters"}
    
    # Check length
    if len(normalized) > 100:
        return {"valid": False, "error": "Platform name is too long"}
    
    return {"valid": True}


def get_platform_suggestions(query: str, limit: int = 10) -> List[Dict[str, str]]:
    """
    Get platform suggestions based on query
    
    Args:
        query: Search query
        limit: Maximum number of suggestions
        
    Returns:
        List of platform suggestions with name, domain, and siteFilter
    """
    if not query:
        return []
    
    normalized_query = normalize_platform_name(query)
    suggestions = []
    
    for key, site_filter in PLATFORM_MAPPINGS.items():
        if normalized_query in key or key in normalized_query:
            domain = site_filter.replace('site:', '')
            suggestions.append({
                'name': key.title(),
                'domain': domain,
                'siteFilter': site_filter
            })
    
    # Sort by relevance (exact matches first, then by length)
    suggestions.sort(key=lambda x: (
        0 if normalized_query in x['name'].lower() else 1,
        len(x['name'])
    ))
    
    return suggestions[:limit]


def process_platform_list(platform_names: List[str]) -> List[str]:
    """
    Process a list of platform names and convert them to site filters
    
    Args:
        platform_names: List of platform names
        
    Returns:
        List of site: filters
    """
    site_filters = []
    seen = set()
    
    for platform_name in platform_names:
        if not platform_name:
            continue
            
        site_filter = convert_platform_to_site_filter(platform_name)
        
        # Avoid duplicates
        if site_filter and site_filter not in seen:
            site_filters.append(site_filter)
            seen.add(site_filter)
    
    return site_filters
