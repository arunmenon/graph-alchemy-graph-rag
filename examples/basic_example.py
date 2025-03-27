#!/usr/bin/env python3
"""
Basic Example - Demonstrates the enhanced Graph RAG system with schema-aware examples.

This script shows how to:
1. Initialize the Graph RAG agent with the new schema-aware components
2. Process questions using dynamically generated examples
3. Display the results
"""

import os
import sys
import logging
import json
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run a basic example of the Graph RAG system."""
    # Import here to handle path issues
    from agents.rag_orchestrator import GraphRAGAgent
    
    # Initialize the Graph RAG agent
    logger.info("Initializing the Graph RAG agent...")
    agent = GraphRAGAgent(preload_schema=True)
    
    # Get a reference to the schema manager
    schema_manager = agent.schema_manager
    
    # Get and log the schema for reference
    logger.info("Loading schema and generating examples...")
    schema = schema_manager.get_schema()
    
    # Get schema-aware examples
    examples = schema_manager.get_examples()
    logger.info(f"Generated {len(examples)} examples")
    
    # Print the examples
    print("\n===== SCHEMA-AWARE EXAMPLES =====")
    for i, example in enumerate(examples, 1):
        print(f"\nExample {i}: {example['question']}")
        for j, query in enumerate(example.get('query_plan', []), 1):
            print(f"  Query {j}: {query.get('purpose', '')}")
            print(f"  Cypher: {query.get('cypher', '')}")
    
    # Sample questions to try
    sample_questions = [
        "What product categories exist in the system?",
        "What are the compliance areas defined in the database?",
        "How are products and compliance areas related?",
    ]
    
    # Display sample questions
    print("\nSample questions:")
    for i, q in enumerate(sample_questions, 1):
        print(f"{i}. {q}")
    
    # Automatically select the first question for testing
    question = sample_questions[0]
    print(f"\n\n===== AUTOMATICALLY SELECTING QUESTION =====\n{question}")
    
    # Process the test question
    print(f"\n\n===== PROCESSING QUESTION =====\n{question}")
    
    # Get the answer
    result = agent.process_question(question)
    
    # Print the result
    print("\n===== QUERY PLAN =====")
    for i, query in enumerate(result.get('query_plan', []), 1):
        print(f"\nQuery {i}: {query.get('purpose', '')}")
        print(f"Cypher: {query.get('cypher', '')}")
    
    print("\n===== THOUGHT PROCESS =====")
    print(result.get('thought_process', ''))
    
    print("\n===== ANSWER =====")
    print(result.get('answer', ''))
    
    # Display evidence if available
    if 'evidence' in result and result['evidence']:
        print("\n===== EVIDENCE =====")
        for item in result['evidence']:
            print(f"- {item}")
    
    # Performance metrics
    print(f"\nProcessing time: {result.get('processing_time', 0):.2f} seconds")
    print(f"Confidence: {result.get('confidence', 0):.2f}")

if __name__ == "__main__":
    # Add the project root to path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    main()