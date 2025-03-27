#!/usr/bin/env python3
"""
Test script for schema-aware example generation.

This script tests the schema-aware example generation capability.
"""

import os
import logging
import json
from schema.manager import SchemaManager
from examples.generators.pattern_generator import PatternExampleGenerator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function to test schema-aware example generation."""
    try:
        # Create a schema manager
        logger.info("Creating schema manager...")
        schema_manager = SchemaManager()
        
        # Get the schema
        logger.info("Loading schema...")
        schema = schema_manager.get_schema(force_refresh=True)
        
        # Get the formatted schema
        formatted_schema = schema_manager.get_formatted_schema()
        logger.info(f"Schema loaded with {len(schema.get('node_types', {}))} node types and {len(schema.get('relationship_types', {}))} relationship types")
        
        # Get examples
        logger.info("Generating examples...")
        examples = schema_manager.get_examples(force_refresh=True)
        
        # Output the examples
        logger.info(f"Generated {len(examples)} examples:")
        for i, example in enumerate(examples, 1):
            logger.info(f"Example {i}:")
            logger.info(f"  Question: {example.get('question', '')}")
            logger.info(f"  Query: {example.get('query', '')}")
            
        # Save examples to file for inspection
        with open('generated_examples.json', 'w') as f:
            json.dump(examples, f, indent=2)
        logger.info("Examples saved to generated_examples.json")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()