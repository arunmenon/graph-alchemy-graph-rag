#!/usr/bin/env python3
"""
End-to-end test for the Graph RAG system with schema-aware example generation.

This script tests the complete pipeline with various sample questions.
"""

import os
import logging
import json
import time
from schema.manager import SchemaManager
from agents.query_decomposition import QueryDecompositionAgent
from agents.graph_retriever import GraphRetrieverAgent
from scripts.client import get_llm_client

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Sample questions for testing
SAMPLE_QUESTIONS = [
    "What are all the tables in the 'Customer' dataset?",
    "How many columns does the 'Orders' table have?",
    "Which tables are related to the 'Product' table?",
    "What are the glossary terms related to 'revenue'?",
    "Which datasets contain tables with more than 10 columns?",
    "What are the business metrics defined in the system?",
    "Show me the relationship between 'Customer' and 'Orders'",
    "List all tables that have a 'created_at' column",
    "What tables belong to the Financial domain?",
    "Which columns in the 'Product' table contain pricing information?",
    "Show me all hierarchical concepts in the system",
    "Which datasets were updated in the last month?",
    "What is the schema of the 'Transaction' table?",
    "Which business processes involve customer data?",
    "How are datasets organized by tenant?"
]

def process_question(question, schema_manager, query_decomposition_agent):
    """
    Process a question through the query decomposition pipeline.
    
    Args:
        question: The natural language question
        schema_manager: The schema manager instance
        query_decomposition_agent: The query decomposition agent
        
    Returns:
        The query decomposition result
    """
    logger.info(f"Processing question: {question}")
    
    # Get examples for prompt enhancement
    examples = schema_manager.get_examples()
    
    # Prepare input for query decomposition
    input_data = {
        'question': question
    }
    
    # Process the question
    start_time = time.time()
    decomposition_result = query_decomposition_agent.process(input_data)
    end_time = time.time()
    
    processing_time = end_time - start_time
    query_plan = decomposition_result.get('query_plan', [])
    
    logger.info(f"Processed in {processing_time:.2f}s, generated {len(query_plan)} queries")
    
    # Return result with metadata
    return {
        'question': question,
        'decomposition_result': decomposition_result,
        'processing_time': processing_time,
        'query_count': len(query_plan)
    }

def main():
    """Main function for E2E testing."""
    try:
        # Get LLM client
        llm_client = get_llm_client()
        
        # Create schema manager
        logger.info("Creating schema manager...")
        schema_manager = SchemaManager(llm_client=llm_client)
        
        # Force refresh schema once
        logger.info("Loading schema (forced refresh)...")
        schema = schema_manager.get_schema(force_refresh=True)
        
        # Create query decomposition agent
        logger.info("Creating query decomposition agent...")
        query_decomposition_agent = QueryDecompositionAgent(schema_manager=schema_manager)
        
        # Process each question
        results = []
        for i, question in enumerate(SAMPLE_QUESTIONS, 1):
            logger.info(f"[{i}/{len(SAMPLE_QUESTIONS)}] Processing question...")
            result = process_question(question, schema_manager, query_decomposition_agent)
            results.append(result)
        
        # Generate summary
        total_time = sum(r['processing_time'] for r in results)
        avg_time = total_time / len(results)
        total_queries = sum(r['query_count'] for r in results)
        avg_queries = total_queries / len(results)
        
        logger.info(f"E2E Test Summary:")
        logger.info(f"Processed {len(results)} questions")
        logger.info(f"Total processing time: {total_time:.2f}s")
        logger.info(f"Average processing time: {avg_time:.2f}s per question")
        logger.info(f"Total generated queries: {total_queries}")
        logger.info(f"Average query count: {avg_queries:.2f} per question")
        
        # Save detailed results to file
        with open('e2e_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        logger.info("Detailed results saved to e2e_test_results.json")
        
        # Print summary of each question
        logger.info("\nIndividual Question Results:")
        for i, result in enumerate(results, 1):
            question = result['question']
            time_taken = result['processing_time']
            query_count = result['query_count']
            query_plan = result['decomposition_result'].get('query_plan', [])
            
            logger.info(f"{i}. {question}")
            logger.info(f"   Time: {time_taken:.2f}s, Queries: {query_count}")
            for j, query in enumerate(query_plan, 1):
                purpose = query.get('purpose', 'Unknown purpose')
                cypher = query.get('cypher', 'No query')
                logger.info(f"   {j}. {purpose}")
                logger.info(f"      {cypher}")
            logger.info("")
            
    except Exception as e:
        logger.error(f"Error in E2E test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()