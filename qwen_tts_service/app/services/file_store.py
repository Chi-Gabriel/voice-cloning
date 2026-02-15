import os
import time
import uuid
import threading
import logging
import shutil
from typing import Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

class FileStore:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FileStore, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        # Store files in /tmp/tts_files
        self.storage_dir = Path("/tmp/tts_files")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # File expiry in seconds (30 minutes)
        self.expiry_seconds = 30 * 60
        
        # Start background cleanup thread
        self._stop_event = threading.Event()
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        
    def save(self, content: bytes, filename: str) -> str:
        """Save content to storage and return a file ID."""
        file_id = str(uuid.uuid4())
        ext = Path(filename).suffix
        if not ext:
            ext = ".wav" # Default to wav if unknown
            
        file_path = self.storage_dir / f"{file_id}{ext}"
        
        with open(file_path, "wb") as f:
            f.write(content)
            
        logger.info(f"Saved file {file_id} ({len(content)} bytes)")
        return file_id

    def get_path(self, file_id: str) -> Optional[Path]:
        """Resolve a file ID to a filesystem path. Returns None if not found."""
        # Search for file with any extension matching the ID
        for file_path in self.storage_dir.glob(f"{file_id}.*"):
            return file_path
        return None

    def _cleanup_loop(self):
        """Background loop to remove expired files."""
        while not self._stop_event.is_set():
            try:
                now = time.time()
                count = 0
                for file_path in self.storage_dir.iterdir():
                    if file_path.is_file():
                        # Check modification time
                        mtime = file_path.stat().st_mtime
                        if now - mtime > self.expiry_seconds:
                            try:
                                file_path.unlink()
                                count += 1
                            except Exception as e:
                                logger.error(f"Failed to delete {file_path}: {e}")
                
                if count > 0:
                    logger.info(f"Cleaned up {count} expired files.")
                    
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                
            # Run every minute
            if self._stop_event.wait(60):
                break

file_store = FileStore()
