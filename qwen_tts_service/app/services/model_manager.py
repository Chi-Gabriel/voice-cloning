import logging
import threading
from typing import Optional

logger = logging.getLogger(__name__)

class ModelManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ModelManager, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance
    
    def _initialize(self):
        self.active_engine: Optional[str] = None # 'tts' or 'asr'
        self.engines = {} # Registry for engines to facilitate cross-unloading
        self.PERSISTENT_ENGINES = {"diarization"} # Engines that stay in VRAM
        
    def register_engine(self, name: str, engine_instance):
        """Register an engine instance (must have an unload() method)."""
        self.engines[name] = engine_instance
        logger.info(f"ModelManager: Registered engine '{name}'")
        
    def acquire(self, name: str):
        """
        Coordinate model swapping. Persistent engines stay loaded.
        Non-persistent engines (TTS/ASR) unload each other.
        """
        # If the requested engine is persistent, just return. 
        # We don't track it as 'active' for swapping purposes.
        if name in self.PERSISTENT_ENGINES:
            logger.info(f"ModelManager: '{name}' is a persistent engine. No swap needed.")
            return

        if self.active_engine == name:
            return
            
        with self._lock:
            # Check other engines
            for engine_name, engine_instance in self.engines.items():
                # Only unload if it's NOT the target AND it's NOT a persistent engine
                if engine_name != name and engine_name not in self.PERSISTENT_ENGINES:
                    logger.info(f"ModelManager: Mutual engine '{name}' acquiring GPU. Unloading '{engine_name}'...")
                    if hasattr(engine_instance, "unload"):
                        engine_instance.unload()
                    elif hasattr(engine_instance, "_unload_all_models"):
                         engine_instance._unload_all_models()
                         
            self.active_engine = name
            logger.info(f"ModelManager: '{name}' is now the active mutual engine.")

model_manager = ModelManager()
