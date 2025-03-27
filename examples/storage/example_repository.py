"""
Example Repository Module - Stores and retrieves generated examples.

This module implements the Repository pattern for example storage and retrieval,
with support for caching and persistence.
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExampleRepositoryInterface:
    """Interface for storing and retrieving examples."""
    
    def get_examples(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get stored examples.
        
        Args:
            force_refresh: Whether to force a refresh
            
        Returns:
            List of examples
        """
        pass
    
    def store_examples(self, examples: List[Dict[str, Any]]) -> bool:
        """
        Store examples.
        
        Args:
            examples: The examples to store
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    def is_stale(self) -> bool:
        """
        Check if the stored examples are stale and should be refreshed.
        
        Returns:
            True if stale, False otherwise
        """
        pass

class FileExampleRepository(ExampleRepositoryInterface):
    """File-based implementation of example repository."""
    
    def __init__(self, storage_path: str, ttl: int = 86400):
        """
        Initialize the file-based repository.
        
        Args:
            storage_path: Path to the storage file
            ttl: Time-to-live in seconds for stored examples
        """
        self.storage_path = storage_path
        self.ttl = ttl
        
        # Create parent directory if it doesn't exist
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
    
    def get_examples(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get stored examples.
        
        Args:
            force_refresh: Whether to force a refresh
            
        Returns:
            List of examples
        """
        if force_refresh or self.is_stale():
            return []
            
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                return data.get('examples', [])
        except Exception as e:
            logger.warning(f"Error reading examples from {self.storage_path}: {e}")
            return []
    
    def store_examples(self, examples: List[Dict[str, Any]]) -> bool:
        """
        Store examples.
        
        Args:
            examples: The examples to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            data = {
                'examples': examples,
                'timestamp': time.time()
            }
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.warning(f"Error storing examples to {self.storage_path}: {e}")
            return False
    
    def is_stale(self) -> bool:
        """
        Check if the stored examples are stale and should be refreshed.
        
        Returns:
            True if stale, False otherwise
        """
        if not os.path.exists(self.storage_path):
            return True
            
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                timestamp = data.get('timestamp', 0)
                return (time.time() - timestamp) > self.ttl
        except Exception as e:
            logger.warning(f"Error checking example staleness: {e}")
            return True

class MemoryExampleRepository(ExampleRepositoryInterface):
    """In-memory implementation of example repository."""
    
    def __init__(self, ttl: int = 3600):
        """
        Initialize the memory repository.
        
        Args:
            ttl: Time-to-live in seconds for stored examples
        """
        self.examples = []
        self.timestamp = 0
        self.ttl = ttl
    
    def get_examples(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get stored examples.
        
        Args:
            force_refresh: Whether to force a refresh
            
        Returns:
            List of examples
        """
        if force_refresh or self.is_stale():
            return []
            
        return self.examples
    
    def store_examples(self, examples: List[Dict[str, Any]]) -> bool:
        """
        Store examples.
        
        Args:
            examples: The examples to store
            
        Returns:
            True if successful, False otherwise
        """
        self.examples = examples
        self.timestamp = time.time()
        return True
    
    def is_stale(self) -> bool:
        """
        Check if the stored examples are stale and should be refreshed.
        
        Returns:
            True if stale, False otherwise
        """
        return (time.time() - self.timestamp) > self.ttl