"""
Schema Cache Module - Handles caching of schema and rich context information.

This module provides caching functionality for schema data, implementing
decorator and repository patterns for efficient storage and retrieval.
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional, Callable

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SchemaCacheInterface:
    """Interface for schema caching functionality."""
    
    def get(self, key: str) -> Any:
        """
        Get an item from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            The cached value or None if not found/expired
        """
        pass
    
    def set(self, key: str, value: Any) -> None:
        """
        Set an item in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
        """
        pass
    
    def is_valid(self, key: str) -> bool:
        """
        Check if a cache entry is valid (exists and not expired).
        
        Args:
            key: The cache key
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    def invalidate(self, key: str = None) -> None:
        """
        Invalidate a cache entry or the entire cache.
        
        Args:
            key: Specific key to invalidate, or None for all
        """
        pass

class MemorySchemaCache(SchemaCacheInterface):
    """In-memory implementation of schema cache."""
    
    def __init__(self, ttl: int = 3600):
        """
        Initialize the memory cache.
        
        Args:
            ttl: Time-to-live in seconds for cache entries
        """
        self.cache = {}
        self.timestamps = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Any:
        """
        Get an item from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            The cached value or None if not found/expired
        """
        if not self.is_valid(key):
            return None
            
        return self.cache.get(key)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set an item in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
        """
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def is_valid(self, key: str) -> bool:
        """
        Check if a cache entry is valid (exists and not expired).
        
        Args:
            key: The cache key
            
        Returns:
            True if valid, False otherwise
        """
        if key not in self.cache or key not in self.timestamps:
            return False
            
        timestamp = self.timestamps.get(key, 0)
        return (time.time() - timestamp) <= self.ttl
    
    def invalidate(self, key: str = None) -> None:
        """
        Invalidate a cache entry or the entire cache.
        
        Args:
            key: Specific key to invalidate, or None for all
        """
        if key is None:
            self.cache.clear()
            self.timestamps.clear()
        elif key in self.cache:
            del self.cache[key]
            if key in self.timestamps:
                del self.timestamps[key]

class FileSchemaCache(SchemaCacheInterface):
    """File-based implementation of schema cache."""
    
    def __init__(self, cache_dir: str, ttl: int = 3600):
        """
        Initialize the file cache.
        
        Args:
            cache_dir: Directory to store cache files
            ttl: Time-to-live in seconds for cache entries
        """
        self.cache_dir = cache_dir
        self.ttl = ttl
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
    
    def get(self, key: str) -> Any:
        """
        Get an item from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            The cached value or None if not found/expired
        """
        if not self.is_valid(key):
            return None
            
        cache_path = os.path.join(self.cache_dir, f"{key}.json")
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
                return cache_data.get('value')
        except Exception as e:
            logger.warning(f"Error reading cache file {cache_path}: {e}")
            return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Set an item in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
        """
        cache_path = os.path.join(self.cache_dir, f"{key}.json")
        try:
            cache_data = {
                'value': value,
                'timestamp': time.time()
            }
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Error writing cache file {cache_path}: {e}")
    
    def is_valid(self, key: str) -> bool:
        """
        Check if a cache entry is valid (exists and not expired).
        
        Args:
            key: The cache key
            
        Returns:
            True if valid, False otherwise
        """
        cache_path = os.path.join(self.cache_dir, f"{key}.json")
        if not os.path.exists(cache_path):
            return False
            
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
                timestamp = cache_data.get('timestamp', 0)
                return (time.time() - timestamp) <= self.ttl
        except Exception as e:
            logger.warning(f"Error reading cache file {cache_path}: {e}")
            return False
    
    def invalidate(self, key: str = None) -> None:
        """
        Invalidate a cache entry or the entire cache.
        
        Args:
            key: Specific key to invalidate, or None for all
        """
        if key is None:
            try:
                for filename in os.listdir(self.cache_dir):
                    if filename.endswith('.json'):
                        os.remove(os.path.join(self.cache_dir, filename))
            except Exception as e:
                logger.warning(f"Error clearing cache directory {self.cache_dir}: {e}")
        else:
            cache_path = os.path.join(self.cache_dir, f"{key}.json")
            if os.path.exists(cache_path):
                try:
                    os.remove(cache_path)
                except Exception as e:
                    logger.warning(f"Error removing cache file {cache_path}: {e}")

class CacheDecorator:
    """Decorator for adding caching to any function."""
    
    def __init__(self, cache: SchemaCacheInterface, key_prefix: str = ""):
        """
        Initialize the cache decorator.
        
        Args:
            cache: The cache implementation to use
            key_prefix: Optional prefix for cache keys
        """
        self.cache = cache
        self.key_prefix = key_prefix
    
    def __call__(self, func: Callable) -> Callable:
        """
        Decorate a function with caching.
        
        Args:
            func: The function to decorate
            
        Returns:
            Decorated function
        """
        def wrapped(*args, force_refresh: bool = False, **kwargs):
            # Generate a cache key from the function name and arguments
            key = f"{self.key_prefix}_{func.__name__}"
            
            # If force refresh, invalidate and don't use cache
            if force_refresh:
                self.cache.invalidate(key)
                result = func(*args, **kwargs)
                self.cache.set(key, result)
                return result
            
            # Check if result is in cache
            cached_result = self.cache.get(key)
            if cached_result is not None:
                return cached_result
            
            # If not in cache, call the function and cache the result
            result = func(*args, **kwargs)
            self.cache.set(key, result)
            return result
            
        return wrapped