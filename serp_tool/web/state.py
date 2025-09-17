"""In-memory web application state.

This module holds simple process-local stores for job metadata and results.
It is intentionally minimal; persistence is out of scope for the web layer.
"""

from typing import Any, Dict, List

from models import SearchJobStatus


# Maps job ID to its status object
job_storage: Dict[str, SearchJobStatus] = {}

# Maps job ID to the list of result item dictionaries
results_storage: Dict[str, List[Dict[str, Any]]] = {}

