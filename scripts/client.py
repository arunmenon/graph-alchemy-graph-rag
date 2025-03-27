"""
LLM Client Module - Provides a client for interacting with OpenAI's API.

This module provides functionality for interacting with OpenAI's API for LLM models.
"""

import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

# Default model to use
DEFAULT_MODEL = "gpt-4o"

def get_llm_client():
    """
    Get an OpenAI client instance.
    
    Returns:
        OpenAI: An initialized OpenAI client
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY environment variable not set. Using default test key.")
        api_key = "sk-test-key"  # This won't work for actual API calls
        
    # Create the client
    client = OpenAI(api_key=api_key)
    
    return client