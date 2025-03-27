#!/usr/bin/env python3
"""
Final test for schema-aware example generation with SchemaManager.

This script tests the complete system with the SchemaManager.
"""

import os
import logging
import json
from schema.manager import SchemaManager
from scripts.client import get_llm_client

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function to test the complete schema-aware example generation."""
    try:
        # Create an LLM client
        llm_client = get_llm_client()
        
        # Create a schema manager with the client
        logger.info("Creating schema manager with LLM client...")
        schema_manager = SchemaManager(llm_client=llm_client, cache_ttl=0)  # No caching for this test
        
        # Get examples with force refresh
        logger.info("Generating examples...")
        examples = schema_manager.get_examples(force_refresh=True)
        
        # Output the examples
        logger.info(f"Generated {len(examples)} examples:")
        for i, example in enumerate(examples, 1):
            logger.info(f"Example {i}:")
            logger.info(f"  Question: {example.get('question', '')}")
            for j, query in enumerate(example.get('query_plan', []), 1):
                logger.info(f"  Query {j}: {query.get('cypher', '')}")
            logger.info(f"  Thought process: {example.get('thought_process', '')[:100]}...")
            
        # Save examples to file for inspection
        with open('final_examples.json', 'w') as f:
            json.dump(examples, f, indent=2)
        logger.info("Examples saved to final_examples.json")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()