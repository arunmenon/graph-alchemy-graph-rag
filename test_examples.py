#!/usr/bin/env python3
"""
Test script for schema-aware example generation.
"""

import os
import logging
import json
from schema.manager import SchemaManager
from examples.generators.pattern_generator import PatternExampleGenerator
import openai

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_llm_client():
    """Simple function to get LLM client"""
    if 'OPENAI_API_KEY' not in os.environ:
        logger.warning("OPENAI_API_KEY not set in environment variables")
        api_key = input("Please enter your OpenAI API key: ")
        os.environ['OPENAI_API_KEY'] = api_key
        
    # Create client using API key
    client = openai.OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    return client

def test_example_generation():
    """Test generating examples for a specific pattern"""
    try:
        # Get LLM client
        llm_client = get_llm_client()
        
        # Create schema manager with client
        logger.info("Creating schema manager...")
        schema_manager = SchemaManager(llm_client=llm_client)
        
        # Get the schema (with refresh)
        logger.info("Loading schema...")
        schema = schema_manager.get_schema(force_refresh=True)
        
        # Get formatted schema
        formatted_schema = schema_manager.get_formatted_schema()
        logger.info(f"Schema loaded with {len(schema.get('node_types', {}))} node types and {len(schema.get('relationship_types', {}))} relationship types")
        
        # Print the relationships
        logger.info("Available relationships:")
        relationships = schema.get('relationships', [])
        for i, rel in enumerate(relationships[:10], 1):  # Show first 10
            logger.info(f"  {i}. {rel}")
            
        # Create a test pattern using the first relationship
        if relationships:
            rel = relationships[0]
            parts = rel.replace('(', '').replace(')', '').split('-[')
            if len(parts) == 2:
                source = parts[0].strip()
                rel_target = parts[1].split(']')
                if len(rel_target) == 2:
                    rel_type = rel_target[0].replace(':', '')
                    target = rel_target[1].replace('->', '').strip()
                    
                    test_pattern = {
                        'source_type': source,
                        'relationship_type': rel_type,
                        'target_type': target,
                        'has_examples': False,
                        'priority': 1
                    }
                    
                    logger.info(f"Using test pattern: {source}-[:{rel_type}]->{target}")
                    
                    # Create pattern generator
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
                    with open('test_examples_output.json', 'w') as f:
                        json.dump(examples, f, indent=2)
                    logger.info("Examples saved to test_examples_output.json")
                    
                    return examples
        else:
            logger.warning("No relationships found in schema")
            
    except Exception as e:
        logger.error(f"Error generating examples: {e}")
        import traceback
        traceback.print_exc()
        
    return []

if __name__ == "__main__":
    test_example_generation()