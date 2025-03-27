#!/usr/bin/env python3
"""
Micro test for schema-aware example generation.

This script directly tests the PatternExampleGenerator with minimal dependencies.
"""

import os
import logging
import json
import time
from openai import OpenAI
from examples.generators.pattern_generator import PatternExampleGenerator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function for minimal example generation test."""
    try:
        # Create OpenAI client directly
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY environment variable not set")
            return
        
        client = OpenAI(api_key=api_key)
        
        # Create a basic example generator
        generator = PatternExampleGenerator(llm_client=client)
        
        # Create a minimal schema and context
        schema = {
            'node_types': {
                'Dataset': ['tenant_id', 'name', 'description', 'created_at', 'updated_at', 'analysis_generated_at', 'domain_analysis'],
                'Table': ['tenant_id', 'name', 'dataset_id', 'description', 'created_at', 'table_type', 'row_count', 'source', 'ddl', 'description_enhanced_at', 'description_enhanced']
            },
            'relationship_types': {
                'CONTAINS': []
            },
            'relationships': [
                '(Dataset)-[:CONTAINS]->(Table)'
            ],
            'node_counts': {
                'Dataset': 4,
                'Table': 19
            }
        }
        
        rich_context = {
            'node_examples': {},
            'relationship_examples': {},
            'common_queries': []
        }
        
        # Create a test pattern
        test_pattern = {
            'source_type': 'Dataset',
            'relationship_type': 'CONTAINS',
            'target_type': 'Table',
            'has_examples': False,
            'priority': 1
        }
        
        # Generate examples
        logger.info("Generating examples for test pattern...")
        start_time = time.time()
        examples = generator._generate_examples_for_pattern(
            pattern=test_pattern,
            schema=schema,
            rich_context=rich_context
        )
        end_time = time.time()
        
        # Output the examples
        logger.info(f"Generated {len(examples)} examples in {end_time - start_time:.2f} seconds:")
        for i, example in enumerate(examples, 1):
            logger.info(f"Example {i}:")
            logger.info(f"  Question: {example.get('question', '')}")
            for j, query in enumerate(example.get('query_plan', []), 1):
                logger.info(f"  Query {j}: {query.get('cypher', '')}")
            
        # Save examples to file for inspection
        with open('micro_example.json', 'w') as f:
            json.dump(examples, f, indent=2)
        logger.info("Examples saved to micro_example.json")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()