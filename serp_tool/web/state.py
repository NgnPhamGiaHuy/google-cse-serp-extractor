from typing import Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime

from models import SearchJobStatus


# In-memory job state (unchanged behavior)
job_storage: Dict[str, SearchJobStatus] = {}
results_storage: Dict[str, List[Dict[str, Any]]] = {}


