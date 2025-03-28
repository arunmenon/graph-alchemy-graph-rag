"""
Embedding Provider Module - Manages text embedding generation.

This module provides abstract and concrete implementations for creating text embeddings
that are used for semantic search operations.
"""

import abc
import logging
import time
from typing import List, Dict, Any, Union, Optional
import numpy as np
from functools import lru_cache

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmbeddingProvider(abc.ABC):
    """Base interface for embedding providers."""

    @abc.abstractmethod
    def encode(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Encode text into embeddings.
        
        Args:
            text: Text string or list of strings to encode
            
        Returns:
            Embedding vectors for the input text
        """
        pass
    
    @abc.abstractmethod
    def batch_encode(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Encode a batch of texts.
        
        Args:
            texts: List of texts to encode
            batch_size: Number of texts to process at once
            
        Returns:
            List of embedding vectors
        """
        pass
    
    @abc.abstractmethod
    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score (higher is more similar)
        """
        pass

class SentenceTransformerProvider(EmbeddingProvider):
    """Embedding provider based on sentence-transformers library."""
    
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5", device: Optional[str] = None,
                cache_size: int = 1000):
        """
        Initialize the sentence transformer embedding provider.
        
        Args:
            model_name: Name of the sentence transformer model to use
            device: Device to run the model on ('cpu', 'cuda', etc.)
            cache_size: Size of the LRU cache for embeddings
        """
        try:
            from sentence_transformers import SentenceTransformer
            import torch
            
            # Determine device if not specified
            if device is None:
                device = "cuda" if torch.cuda.is_available() else "cpu"
                
            # Log the device being used
            logger.info(f"Using device {device} for embedding model")
            
            # Initialize the model
            self.model = SentenceTransformer(model_name, device=device)
            self.model_name = model_name
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            self.device = device
            
            logger.info(f"Loaded sentence transformer model {model_name} with {self.embedding_dim} dimensions")
            
            # Set up caching
            self.encode_single = lru_cache(maxsize=cache_size)(self._encode_single)
            
        except ImportError:
            logger.error("sentence-transformers library not installed. Please install with 'pip install sentence-transformers'")
            raise
    
    def _encode_single(self, text: str) -> List[float]:
        """Internal method for encoding a single text string."""
        return self.model.encode(text).tolist()
    
    def encode(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Encode text into embeddings with caching for single texts.
        
        Args:
            text: Text string or list of strings to encode
            
        Returns:
            Embedding vectors for the input text
        """
        if isinstance(text, str):
            return self.encode_single(text)
        else:
            return self.batch_encode(text)
    
    def batch_encode(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Encode a batch of texts.
        
        Args:
            texts: List of texts to encode
            batch_size: Number of texts to process at once
            
        Returns:
            List of embedding vectors
        """
        start_time = time.time()
        logger.info(f"Encoding batch of {len(texts)} texts with batch size {batch_size}")
        
        embeddings = self.model.encode(texts, batch_size=batch_size).tolist()
        
        elapsed = time.time() - start_time
        logger.info(f"Batch encoding completed in {elapsed:.2f}s ({len(texts)/elapsed:.2f} texts/s)")
        
        return embeddings
    
    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (higher is more similar)
        """
        # Convert to numpy arrays for calculation
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Compute cosine similarity
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        
        return float(similarity)

class DummyEmbeddingProvider(EmbeddingProvider):
    """Dummy embedding provider for testing or when dependencies aren't available."""
    
    def __init__(self, dimension: int = 384):
        """
        Initialize the dummy embedding provider.
        
        Args:
            dimension: Dimensionality of the generated embeddings
        """
        self.dimension = dimension
        logger.warning("Using DummyEmbeddingProvider - generates random embeddings for testing only!")
    
    def encode(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate random embeddings for text.
        
        Args:
            text: Text string or list of strings to encode
            
        Returns:
            Random embedding vectors
        """
        if isinstance(text, str):
            return [float(i) for i in np.random.randn(self.dimension)]
        else:
            return self.batch_encode(text)
    
    def batch_encode(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate random embeddings for a batch of texts.
        
        Args:
            texts: List of texts to encode
            batch_size: Not used in the dummy implementation
            
        Returns:
            List of random embedding vectors
        """
        return [[float(i) for i in np.random.randn(self.dimension)] for _ in range(len(texts))]
    
    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Random similarity score between 0 and 1
        """
        return float(np.random.random())