"""
Environment configuration and settings management (YAML + .env with env overrides)
"""

from .core import Config

# Global configuration instance (backward-compatible)
config = Config()

__all__ = ["Config", "config"]


