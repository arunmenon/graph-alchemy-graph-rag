"""
Base Generator Module - Abstract base class for example generators.

This module provides the foundation for different example generation strategies,
implementing the Strategy and Template Method patterns.
"""

import abc
import logging
from typing import Dict, List, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExampleGeneratorInterface(abc.ABC):
    """Interface for generating question-answer examples."""
    
    @abc.abstractmethod
    def generate_examples(self, schema: Dict[str, Any], rich_context: Dict[str, Any], count: int = 3) -> List[Dict[str, Any]]:
        """
        Generate question-answer examples based on schema and context.
        
        Args:
            schema: The graph schema
            rich_context: Additional context like node/relationship examples
            count: Number of examples to generate
            
        Returns:
            List of examples (each with question, query_plan, thought_process)
        """
        pass
    
    @abc.abstractmethod
    def validate_examples(self, examples: List[Dict[str, Any]], db_connector) -> List[Dict[str, Any]]:
        """
        Validate examples against the database.
        
        Args:
            examples: List of generated examples
            db_connector: Database connector for validation
            
        Returns:
            List of validated examples
        """
        pass

class BaseExampleGenerator(ExampleGeneratorInterface):
    """Base implementation with common functionality for example generators."""
    
    def __init__(self, llm_client=None):
        """
        Initialize the base example generator.
        
        Args:
            llm_client: Client for LLM API calls
        """
        self.llm_client = llm_client
    
    def generate_examples(self, schema: Dict[str, Any], rich_context: Dict[str, Any], count: int = 3) -> List[Dict[str, Any]]:
        """
        Generate question-answer examples based on schema and context.
        
        Args:
            schema: The graph schema
            rich_context: Additional context like node/relationship examples
            count: Number of examples to generate
            
        Returns:
            List of examples (each with question, query_plan, thought_process)
        """
        # Identify key patterns for examples
        key_patterns = self._identify_key_patterns(schema, rich_context)
        
        # Generate examples for each pattern
        all_examples = []
        for pattern in key_patterns[:count]:
            examples = self._generate_examples_for_pattern(pattern, schema, rich_context)
            all_examples.extend(examples)
            
            # Break if we have enough examples
            if len(all_examples) >= count:
                break
        
        # Return the requested number of examples
        return all_examples[:count]
    
    def validate_examples(self, examples: List[Dict[str, Any]], db_connector) -> List[Dict[str, Any]]:
        """
        Validate examples against the database.
        
        Args:
            examples: List of generated examples
            db_connector: Database connector for validation
            
        Returns:
            List of validated examples
        """
        validated_examples = []
        
        for example in examples:
            # Get the query plan from the example
            query_plan = example.get('query_plan', [])
            if not query_plan:
                continue
            
            # Check each query in the plan
            valid = True
            for query_item in query_plan:
                cypher = query_item.get('cypher', '')
                if not cypher:
                    valid = False
                    break
                
                # Try to execute the query
                try:
                    # Add LIMIT if not present to avoid large result sets
                    test_query = cypher
                    if "LIMIT" not in test_query.upper():
                        test_query += " LIMIT 5"
                    
                    # Execute the query
                    result = db_connector.execute_query(test_query)
                    
                    # Check if we got results
                    if not result or len(result) == 0:
                        valid = False
                        break
                except Exception as e:
                    logger.warning(f"Invalid query: {e}")
                    valid = False
                    break
            
            # If valid, add to validated examples
            if valid:
                validated_examples.append(example)
        
        return validated_examples
    
    @abc.abstractmethod
    def _identify_key_patterns(self, schema: Dict[str, Any], rich_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify key patterns for examples.
        
        Args:
            schema: The graph schema
            rich_context: Additional context
            
        Returns:
            List of key patterns to use for examples
        """
        pass
    
    @abc.abstractmethod
    def _generate_examples_for_pattern(self, pattern: Dict[str, Any], schema: Dict[str, Any], rich_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate examples for a specific pattern.
        
        Args:
            pattern: The pattern to generate examples for
            schema: The graph schema
            rich_context: Additional context
            
        Returns:
            List of examples for this pattern
        """
        pass