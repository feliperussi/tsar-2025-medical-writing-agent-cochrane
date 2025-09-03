import os
from typing import Optional
from api.tools.glossary_service.glossary_service import GlossaryService


class GlossaryServiceSingleton:
    """Singleton wrapper for GlossaryService to avoid re-indexing on every request"""
    
    _instance: Optional['GlossaryServiceSingleton'] = None
    _service: Optional[GlossaryService] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_service(self) -> Optional[GlossaryService]:
        """Get or create the GlossaryService instance"""
        if not self._initialized:
            glossaries_dir = os.getenv("GLOSSARIES_DIR", "./api/tools/glossary_service/glossaries")
            try:
                print("Initializing GlossaryService singleton...")
                self._service = GlossaryService(glossaries_dir)
                self._initialized = True
                print("GlossaryService singleton initialized successfully.")
            except Exception as e:
                print(f"Warning: Could not initialize GlossaryService singleton: {e}")
                self._service = None
                self._initialized = True  # Mark as initialized even on failure to avoid retrying
        
        return self._service
    
    def reset(self):
        """Reset the singleton (useful for testing)"""
        self._service = None
        self._initialized = False


# Global singleton instance
glossary_singleton = GlossaryServiceSingleton()