"""
Example Generator Factory Module - Creates appropriate example generators.

This module implements the Factory pattern for creating example generators
based on configuration and available data.
"""

import logging
from typing import Dict, Any, Optional

from .generators.base_generator import ExampleGeneratorInterface
from .generators.pattern_generator import PatternExampleGenerator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExampleGeneratorFactory:
    """Factory for creating example generators."""
    
    @staticmethod
    def create_generator(generator_type: str, config: Dict[str, Any] = None, llm_client=None) -> ExampleGeneratorInterface:
        """
        Create an example generator based on type.
        
        Args:
            generator_type: Type of generator to create
            config: Configuration for the generator
            llm_client: Client for LLM API calls
            
        Returns:
            Example generator instance
        """
        config = config or {}
        
        if generator_type == 'pattern':
            return PatternExampleGenerator(llm_client=llm_client)
        else:
            logger.warning(f"Unknown generator type: {generator_type}, defaulting to pattern generator")
            return PatternExampleGenerator(llm_client=llm_client)