"""
LLM Client Module - Provides a client for interacting with LLM services.

This module provides a unified interface for interacting with various LLM services.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Union
from openai import OpenAI

logger = logging.getLogger(__name__)

def get_default_client():
    """
    Get the default LLM client (currently OpenAI).
    
    Returns:
        A client instance for the default LLM service
    """
    return get_openai_client()

def get_openai_client():
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