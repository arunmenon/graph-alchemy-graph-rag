#!/usr/bin/env python3
"""
Simplified test for schema-aware example generation.

This script tests generating a single example.
"""

import os
import logging
import json
from schema.manager import SchemaManager
from examples.generators.pattern_generator import PatternExampleGenerator
from scripts.client import get_llm_client

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function to test a simplified example generation."""
    try:
        # Create a schema manager
        logger.info("Creating schema manager...")
        
        # Get LLM client
        llm_client = get_llm_client()
        
        # Create schema manager with client
        schema_manager = SchemaManager(llm_client=llm_client)
        
        # Get the schema
        logger.info("Loading schema...")
        schema = schema_manager.get_schema(force_refresh=True)
        
        # Get the formatted schema
        formatted_schema = schema_manager.get_formatted_schema()
        logger.info(f"Schema loaded with {len(schema.get('node_types', {}))} node types and {len(schema.get('relationship_types', {}))} relationship types")
        
        # Create a simple pattern for testing
        test_pattern = {
            'source_type': 'Dataset',
            'relationship_type': 'CONTAINS',
            'target_type': 'Table',
            'has_examples': False,
            'priority': 1
        }
        
        # Create a pattern generator
        generator = PatternExampleGenerator(llm_client=llm_client)
        
        # Empty rich context for testing
        rich_context = {
            'node_examples': {},
            'relationship_examples': {},
            'common_queries': []
        }
        
        # Generate examples for this pattern
        logger.info("Generating examples for test pattern...")
        examples = generator._generate_examples_for_pattern(
            pattern=test_pattern,
            schema=schema,
            rich_context=rich_context
        )
        
        # Output the examples
        logger.info(f"Generated {len(examples)} examples:")
        for i, example in enumerate(examples, 1):
            logger.info(f"Example {i}:")
            logger.info(f"  Question: {example.get('question', '')}")
            for j, query in enumerate(example.get('query_plan', []), 1):
                logger.info(f"  Query {j}: {query.get('cypher', '')}")
            
        # Save examples to file for inspection
        with open('test_example.json', 'w') as f:
            json.dump(examples, f, indent=2)
        logger.info("Examples saved to test_example.json")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()