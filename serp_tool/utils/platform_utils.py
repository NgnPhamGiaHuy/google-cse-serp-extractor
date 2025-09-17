import re
from typing import Any, Dict, List, Optional


PLATFORM_MAPPINGS = {

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


    'github': 'site:github.com',
    'stack overflow': 'site:stackoverflow.com',
    'dev.to': 'site:dev.to',
    'hackernews': 'site:news.ycombinator.com',
    'reddit': 'site:reddit.com',


    'youtube': 'site:youtube.com',
    'vimeo': 'site:vimeo.com',
    'twitch': 'site:twitch.tv',
    'medium': 'site:medium.com',
    'flickr': 'site:flickr.com',


    'behance': 'site:behance.net',
    'dribbble': 'site:dribbble.com',


    'crunchbase': 'site:crunchbase.com',
    'angellist': 'site:angel.co',
    'producthunt': 'site:producthunt.com',
    'kickstarter': 'site:kickstarter.com',
    'indiegogo': 'site:indiegogo.com',
    'patreon': 'site:patreon.com',


    'quora': 'site:quora.com',
    'slideshare': 'site:slideshare.net',
    'scribd': 'site:scribd.com',
    'issuu': 'site:issuu.com',


    'academia': 'site:academia.edu',
    'researchgate': 'site:researchgate.net',
    'orcid': 'site:orcid.org',
    'scholar': 'site:scholar.google.com',
    'arxiv': 'site:arxiv.org',
    'pubmed': 'site:pubmed.ncbi.nlm.nih.gov',


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
    if not platform_name:
        return ""


    normalized = platform_name.lower().strip()


    prefixes_to_remove = ['www.', 'http://', 'https://', 'site:']
    for prefix in prefixes_to_remove:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):]


    normalized = re.sub(r'/+$', '', normalized)
    normalized = re.sub(r'/(in|profile|user|u)/?$', '', normalized)

    return normalized


def convert_platform_to_site_filter(platform_name: str) -> str:
    if not platform_name:
        return ""


    if platform_name.lower().startswith('site:'):
        return platform_name

    normalized = normalize_platform_name(platform_name)


    if normalized in PLATFORM_MAPPINGS:
        return PLATFORM_MAPPINGS[normalized]


    for key, value in PLATFORM_MAPPINGS.items():
        if normalized in key or key in normalized:
            return value


    if '.' in normalized and not normalized.startswith('site:'):

        domain = normalized


        if 'linkedin' in domain and not domain.endswith('/in'):
            if not domain.endswith('/'):
                domain += '/'
            domain += 'in'

        return f"site:{domain}"


    if not '.' in normalized and not ' ' in normalized:
        return f"site:{normalized}.com"


    return f"site:{normalized}"


def validate_platform_name(platform_name: str) -> Dict[str, Any]:
    if not platform_name or not platform_name.strip():
        return {"valid": False, "error": "Platform name cannot be empty"}

    normalized = normalize_platform_name(platform_name)


    if not re.match(r'^[a-zA-Z0-9\s\.\-_\/]+$', normalized):
        return {"valid": False, "error": "Platform name contains invalid characters"}


    if len(normalized) > 100:
        return {"valid": False, "error": "Platform name is too long"}

    return {"valid": True}


def get_platform_suggestions(query: str, limit: int = 10) -> List[Dict[str, str]]:
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


    suggestions.sort(key=lambda x: (
        0 if normalized_query in x['name'].lower() else 1,
        len(x['name'])
    ))

    return suggestions[:limit]


def process_platform_list(platform_names: List[str]) -> List[str]:
    site_filters = []
    seen = set()

    for platform_name in platform_names:
        if not platform_name:
            continue

        site_filter = convert_platform_to_site_filter(platform_name)


        if site_filter and site_filter not in seen:
            site_filters.append(site_filter)
            seen.add(site_filter)

    return site_filters
