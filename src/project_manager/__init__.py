"""Project Manager package."""

from project_manager.core.settings import Settings, get_settings
from project_manager.utils.logging import get_logger, setup_logging

__version__ = "0.1.0"

__all__ = [
    "Settings",
    "get_logger",
    "get_settings",
    "setup_logging",
]
