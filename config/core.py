import os
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv, dotenv_values
import yaml


def _bool_env(value: Optional[str], default: bool = False) -> bool:
    """Parse common boolean-like env values."""
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes", "on")


def _deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge dict b into a, returning a new dict."""
    out = dict(a)
    for k, v in (b or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


class Config:
    """Application configuration with centralized YAML file and environment variable support.

    Resolution order (lowest to highest precedence):
    1) Built-in defaults
    2) config.yaml (if present)
    3) .env / .env.local files
    4) Process environment variables
    """

    def __init__(self):
        self._project_root = Path(__file__).parent.parent
        self._data: Dict[str, Any] = {}
        self._load_environment_files()
        self._load_yaml()

    # ---------- Loading ----------
    def _load_environment_files(self) -> None:
        """Load environment variables from .env and .env.local (if present)."""
        env_file = self._project_root / ".env"
        if env_file.exists():
            load_dotenv(env_file, override=True)
        env_local_file = self._project_root / ".env.local"
        if env_local_file.exists():
            load_dotenv(env_local_file, override=True)

    def _load_yaml(self) -> None:
        """Load config.yaml if present and apply defaults and env overrides."""
        cfg_path = self._project_root / "config.yaml"
        if cfg_path.exists():
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    file_cfg = yaml.safe_load(f) or {}
            except Exception:
                file_cfg = {}
        else:
            file_cfg = {}

        defaults: Dict[str, Any] = {
            "api": {
                "provider_order": ["google"],
                "google": {
                    "base_url": "https://www.googleapis.com/customsearch/v1",
                    "apply_locale_hints": False,
                },
            },
            "search": {
                "results_per_page": 10,
                "max_pages": 1,
                "country": None,
                "language": None,
                "safe_search": None,
                "time_range": None,
            },
            "io": {
                "input_types": ["json", "csv", "xlsx"],
                "output_formats": ["json", "csv", "xlsx"],
                "export_dir": "downloads",
                "filename_pattern": "search_results_{job}_{timestamp}",
            },
            "normalization": {
                "unified_schema": ["title", "url", "snippet", "position", "type"],
                "missing_field_value": None,
            },
            "behavior": {
                "max_retries": 2,
                "delay_ms": 1000,
                "fallback_strategy": "sequential",
            },
            "logging": {
                "level": os.getenv("LOG_LEVEL", "INFO").upper(),
                "file": str((self._project_root / "logs" / "app.log").as_posix()),
                "console": True,
            },
            "caching": {
                "enabled": True,
                "dir": None,  # Will be set dynamically by temp_manager
                "ttl_seconds": int(os.getenv("CACHE_TTL_SECONDS", "86400")),
            },
        }

        merged = _deep_merge(defaults, file_cfg)

        # Apply env overrides for secrets and common toggles
        merged.setdefault("api", {}).setdefault("google", {})["api_key"] = os.getenv("GOOGLE_API_KEY") or merged["api"]["google"].get("api_key")
        merged["api"]["google"]["cx"] = os.getenv("GOOGLE_CSE_CX") or os.getenv("GOOGLE_CX") or merged["api"]["google"].get("cx")

        if os.getenv("DEBUG") is not None:
            merged.setdefault("logging", {})["level"] = "DEBUG" if _bool_env(os.getenv("DEBUG"), False) else merged["logging"].get("level", "INFO")
        if os.getenv("APPLY_LOCALE_HINTS") is not None:
            merged["api"]["google"]["apply_locale_hints"] = _bool_env(os.getenv("APPLY_LOCALE_HINTS"), False)
        if os.getenv("REQUEST_TIMEOUT"):
            merged.setdefault("behavior", {})["request_timeout_seconds"] = int(os.getenv("REQUEST_TIMEOUT", "300"))
        if os.getenv("MAX_CONCURRENT_JOBS"):
            merged.setdefault("behavior", {})["max_concurrent_jobs"] = int(os.getenv("MAX_CONCURRENT_JOBS", "5"))

        self._data = merged

    # ---------- Helpers ----------
    def _get(self, path: str, default: Any = None) -> Any:
        cur: Any = self._data
        for part in path.split('.'):
            if not isinstance(cur, dict):
                return default
            cur = cur.get(part)
            if cur is None:
                return default
        return cur

    # ---------- Backward-compatible properties ----------

    @property
    def google_api_key(self) -> Optional[str]:
        # Try token manager first, then fall back to config
        try:
            from serp_tool.utils.token_manager import token_manager
            token = token_manager.get_token('google_api_key')
            if token:
                return token
        except ImportError:
            pass
        return self._get("api.google.api_key")

    @property
    def google_cx(self) -> Optional[str]:
        # Try token manager first, then fall back to config
        try:
            from serp_tool.utils.token_manager import token_manager
            token = token_manager.get_token('google_cx')
            if token:
                return token
        except ImportError:
            pass
        return self._get("api.google.cx")

    @property
    def debug(self) -> bool:
        return self.log_level == "DEBUG"

    @property
    def log_level(self) -> str:
        return (self._get("logging.level", "INFO") or "INFO").upper()

    @property
    def max_concurrent_jobs(self) -> int:
        return int(self._get("behavior.max_concurrent_jobs", os.getenv('MAX_CONCURRENT_JOBS', '5')))

    @property
    def request_timeout(self) -> int:
        return int(self._get("behavior.request_timeout_seconds", os.getenv('REQUEST_TIMEOUT', '300')))

    @property
    def apply_locale_hints(self) -> bool:
        return bool(self._get("api.google.apply_locale_hints", False))

    # ---------- New structured getters ----------
    @property
    def google_base_url(self) -> str:
        return self._get("api.google.base_url", "https://www.googleapis.com/customsearch/v1")


    @property
    def provider_order(self) -> list:
        return list(self._get("api.provider_order", ["google"]))

    @property
    def search_defaults(self) -> Dict[str, Any]:
        return dict(self._get("search", {}))

    @property
    def io_settings(self) -> Dict[str, Any]:
        return dict(self._get("io", {}))

    @property
    def normalization_settings(self) -> Dict[str, Any]:
        return dict(self._get("normalization", {}))

    @property
    def behavior_settings(self) -> Dict[str, Any]:
        return dict(self._get("behavior", {}))

    @property
    def logging_settings(self) -> Dict[str, Any]:
        return dict(self._get("logging", {}))

    @property
    def caching_settings(self) -> Dict[str, Any]:
        return dict(self._get("caching", {}))

    # ---------- Validation & Diagnostics ----------
    def validate_required(self) -> None:
        has_google = bool(self.google_api_key and self.google_cx)
        if not has_google:
            raise ValueError(
                "No scraping provider configured. Provide GOOGLE_API_KEY and GOOGLE_CSE_CX for Google CSE."
            )

    def get_env_info(self) -> dict:
        return {
            'google_api_key_set': bool(self.google_api_key),
            'google_cx_set': bool(self.google_cx),
            'debug_mode': self.debug,
            'log_level': self.log_level,
            'max_concurrent_jobs': self.max_concurrent_jobs,
            'request_timeout': self.request_timeout,
            'env_file_exists': (self._project_root / ".env").exists(),
            'env_local_file_exists': (self._project_root / ".env.local").exists(),
            'yaml_exists': (self._project_root / "config.yaml").exists(),
        }



