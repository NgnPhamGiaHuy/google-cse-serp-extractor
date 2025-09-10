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
    """Manages temporary directories with automatic cleanup on application shutdown.
    
    This class provides a centralized way to manage temporary directories that are
    automatically cleaned up when the application stops, restarts, or shuts down.
    It uses Python's tempfile module for cross-platform compatibility and proper
    temporary directory handling.
    """
    
    _instance: Optional['TempDirectoryManager'] = None
    _temp_dir: Optional[Path] = None
    _cleanup_registered = False
    
    def __new__(cls) -> 'TempDirectoryManager':
        """Singleton pattern to ensure only one temp manager exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the temp directory manager."""
        if not self._cleanup_registered:
            self._register_cleanup_handlers()
            self._cleanup_registered = True
    
    def _register_cleanup_handlers(self) -> None:
        """Register cleanup handlers for various shutdown scenarios."""
        # Register cleanup for normal exit
        atexit.register(self.cleanup)
        
        # Register cleanup for signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # For Windows compatibility
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, self._signal_handler)
    
    def _signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signals."""
        app_logger.info(f"Received signal {signum}, cleaning up temporary directories...")
        self.cleanup()
        sys.exit(0)
    
    def get_temp_dir(self) -> Path:
        """Get the temporary directory, creating it if necessary.
        
        Returns:
            Path: The temporary directory path
        """
        if self._temp_dir is None or not self._temp_dir.exists():
            self._create_temp_dir()
        return self._temp_dir
    
    def _create_temp_dir(self) -> None:
        """Create a new temporary directory using tempfile.mkdtemp."""
        try:
            # Create a temporary directory with a descriptive prefix
            temp_path = tempfile.mkdtemp(prefix="serp_tool_", suffix="_temp")
            self._temp_dir = Path(temp_path)
            
            # Create subdirectories that the application expects
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
            # Fallback to a local temp directory
            self._temp_dir = Path("temp")
            self._temp_dir.mkdir(exist_ok=True)
            (self._temp_dir / "cse_cache").mkdir(exist_ok=True)
            (self._temp_dir / "inspections").mkdir(exist_ok=True)
    
    def cleanup(self) -> None:
        """Clean up the temporary directory and all its contents."""
        if self._temp_dir and self._temp_dir.exists():
            try:
                # Clean up tokens before removing the directory
                try:
                    from serp_tool.utils.token_manager import token_manager
                    token_manager.clear_all_tokens()
                except ImportError:
                    pass  # Token manager not available
                
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
        """Get the cache subdirectory within the temp directory.
        
        Returns:
            Path: The cache directory path
        """
        temp_dir = self.get_temp_dir()
        cache_dir = temp_dir / "cse_cache"
        cache_dir.mkdir(exist_ok=True)
        return cache_dir
    
    def get_inspections_dir(self) -> Path:
        """Get the inspections subdirectory within the temp directory.
        
        Returns:
            Path: The inspections directory path
        """
        temp_dir = self.get_temp_dir()
        inspections_dir = temp_dir / "inspections"
        inspections_dir.mkdir(exist_ok=True)
        return inspections_dir
    
    @contextmanager
    def get_temp_file(self, suffix: str = "", prefix: str = "temp_") -> Path:
        """Context manager for creating temporary files.
        
        Args:
            suffix: File suffix (e.g., '.json', '.csv')
            prefix: File prefix
            
        Yields:
            Path: Path to the temporary file
        """
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


# Global instance
temp_manager = TempDirectoryManager()


def get_temp_dir() -> Path:
    """Get the temporary directory.
    
    Returns:
        Path: The temporary directory path
    """
    return temp_manager.get_temp_dir()


def get_cache_dir() -> Path:
    """Get the cache directory.
    
    Returns:
        Path: The cache directory path
    """
    return temp_manager.get_cache_dir()


def get_inspections_dir() -> Path:
    """Get the inspections directory.
    
    Returns:
        Path: The inspections directory path
    """
    return temp_manager.get_inspections_dir()


def cleanup_temp_dir() -> None:
    """Clean up the temporary directory.
    
    This function can be called manually if needed, though cleanup
    is automatically handled on application shutdown.
    """
    temp_manager.cleanup()
