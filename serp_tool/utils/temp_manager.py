import os
import shutil
import tempfile
import atexit
import signal
import sys
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from serp_tool.logging import app_logger


class TempDirectoryManager:

    _instance: Optional['TempDirectoryManager'] = None
    _temp_dir: Optional[Path] = None
    _cleanup_registered = False

    def __new__(cls) -> 'TempDirectoryManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._cleanup_registered:
            self._register_cleanup_handlers()
            self._cleanup_registered = True

    def _register_cleanup_handlers(self) -> None:
        """Register process exit and signal handlers for cleanup."""
        atexit.register(self.cleanup)

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, self._signal_handler)

    def _signal_handler(self, signum: int, frame) -> None:
        app_logger.info(f"Received signal {signum}, cleaning up temporary directories...")
        self.cleanup()
        sys.exit(0)

    def get_temp_dir(self) -> Path:
        if self._temp_dir is None or not self._temp_dir.exists():
            self._create_temp_dir()
        return self._temp_dir

    def _create_temp_dir(self) -> None:
        try:
            temp_path = tempfile.mkdtemp(prefix="serp_tool_", suffix="_temp")
            self._temp_dir = Path(temp_path)

            (self._temp_dir / "cse_cache").mkdir(exist_ok=True)
            (self._temp_dir / "inspections").mkdir(exist_ok=True)

            app_logger.info(
                f"Created temporary directory: {self._temp_dir}",
                extra={"action": "temp_dir_create", "status": "success", "path": str(self._temp_dir)}
            )
        except Exception as e:
            app_logger.error(
                f"Failed to create temporary directory: {e}",
                extra={"action": "temp_dir_create", "status": "fail"}
            )

            self._temp_dir = Path("temp")
            self._temp_dir.mkdir(exist_ok=True)
            (self._temp_dir / "cse_cache").mkdir(exist_ok=True)
            (self._temp_dir / "inspections").mkdir(exist_ok=True)

    def cleanup(self) -> None:
        if self._temp_dir and self._temp_dir.exists():
            try:
                try:
                    from serp_tool.utils.token_manager import token_manager
                    token_manager.clear_all_tokens()
                except ImportError:
                    pass

                shutil.rmtree(self._temp_dir)
                app_logger.info(
                    f"Cleaned up temporary directory: {self._temp_dir}",
                    extra={"action": "temp_dir_cleanup", "status": "success", "path": str(self._temp_dir)}
                )
            except Exception as e:
                app_logger.warning(
                    f"Failed to clean up temporary directory {self._temp_dir}: {e}",
                    extra={"action": "temp_dir_cleanup", "status": "fail", "path": str(self._temp_dir)}
                )
            finally:
                self._temp_dir = None

    def get_cache_dir(self) -> Path:
        temp_dir = self.get_temp_dir()
        cache_dir = temp_dir / "cse_cache"
        cache_dir.mkdir(exist_ok=True)
        return cache_dir

    def get_inspections_dir(self) -> Path:
        temp_dir = self.get_temp_dir()
        inspections_dir = temp_dir / "inspections"
        inspections_dir.mkdir(exist_ok=True)
        return inspections_dir

    @contextmanager
    def get_temp_file(self, suffix: str = "", prefix: str = "temp_") -> Path:
        temp_file = None
        try:
            temp_file = tempfile.NamedTemporaryFile(
                dir=self.get_temp_dir(),
                prefix=prefix,
                suffix=suffix,
                delete=False
            )
            temp_file.close()
            yield Path(temp_file.name)
        finally:
            if temp_file and Path(temp_file.name).exists():
                try:
                    Path(temp_file.name).unlink()
                except Exception:
                    pass


temp_manager = TempDirectoryManager()


def get_temp_dir() -> Path:
    return temp_manager.get_temp_dir()


def get_cache_dir() -> Path:
    return temp_manager.get_cache_dir()


def get_inspections_dir() -> Path:
    return temp_manager.get_inspections_dir()


def cleanup_temp_dir() -> None:
    temp_manager.cleanup()
