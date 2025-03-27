#!/usr/bin/env python3
"""
Test a single query through the entire pipeline.

This script tests a single natural language query to verify schema-aware examples
work correctly.
"""

import os
import logging
import json
import time
from schema.manager import SchemaManager
from agents.query_decomposition import QueryDecompositionAgent
from scripts.client import get_llm_client

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Skip schema loading to reduce log output
logging.getLogger('graph_db.neo4j_database').setLevel(logging.WARNING)

def main():
    """Main function to test a single query."""
    try:
        # Get LLM client
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY environment variable not set")
            return
        
        llm_client = get_llm_client()
        
        # Create schema manager with the client
        logger.info("Creating schema manager with LLM client...")
        schema_manager = SchemaManager(llm_client=llm_client)
        
        # Initial schema load
        logger.info("Loading schema...")
        schema = schema_manager.get_schema()
        
        # Create query decomposition agent
        logger.info("Creating query decomposition agent...")
        query_decomposition_agent = QueryDecompositionAgent(schema_manager=schema_manager)
        
        # The question to process
        question = "Find tables that contain sensitive customer data like PII, and identify which business metrics and processes are dependent on this data"
        
        # Process the question
        logger.info(f"Processing question: {question}")
        start_time = time.time()
        
        # Prepare input for query decomposition
        input_data = {
            'question': question
        }
        
        # Process the query
        result = query_decomposition_agent.process(input_data)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Output the result
        logger.info(f"Processed in {processing_time:.2f} seconds")
        
        query_plan = result.get('query_plan', [])
        logger.info(f"Generated {len(query_plan)} queries:")
        
        for i, query in enumerate(query_plan, 1):
            purpose = query.get('purpose', 'Unknown purpose')
            cypher = query.get('cypher', 'No query')
            logger.info(f"{i}. {purpose}")
            logger.info(f"   {cypher}")
        
        # Save the result to file
        with open('single_query_result.json', 'w') as f:
            json.dump(result, f, indent=2)
        logger.info("Result saved to single_query_result.json")
        
        # Log thought process
        thought_process = result.get('thought_process', '')
        if thought_process:
            logger.info(f"Thought process: {thought_process[:200]}...")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()