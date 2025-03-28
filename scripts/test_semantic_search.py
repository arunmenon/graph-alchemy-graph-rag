"""
Test Semantic Search Script - Demonstrates the semantic search functionality.

This script runs a semantic search test on a sample question and shows how semantic
search enhances the graph retrieval process.
"""

import os
import sys
import logging
import argparse
import json
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('semantic_search_test.log')
    ]
)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from graph_rag.workflow_manager import WorkflowManager
from agents.query_decomposition import QueryDecompositionAgent
from agents.graph_retriever import GraphRetrieverAgent
from agents.reasoning import ReasoningAgent
from semantic.embedding_provider import DummyEmbeddingProvider
from graph_db.graph_strategy_factory import GraphDatabaseFactory

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test semantic search functionality")
    
    parser.add_argument(
        "question",
        nargs="?",
        default="What tables are related to Work Orders?",
        help="Question to test (default: 'What tables are related to Work Orders?')"
    )
    
    parser.add_argument(
        "--no-semantic",
        action="store_true",
        help="Disable semantic search for comparison"
    )
    
    parser.add_argument(
        "--output",
        default="semantic_search_results.json",
        help="Output file for results (default: semantic_search_results.json)"
    )
    
    return parser.parse_args()

def create_workflow(enable_semantic_search: bool) -> WorkflowManager:
    """Create and configure the workflow."""
    # Create workflow
    workflow = WorkflowManager("graph_rag")
    
    # Add agents to workflow
    workflow.add_agent(QueryDecompositionAgent())
    workflow.add_agent(GraphRetrieverAgent(enable_semantic_search=enable_semantic_search))
    workflow.add_agent(ReasoningAgent())
    
    return workflow

def run_test(question: str, enable_semantic_search: bool) -> Dict[str, Any]:
    """Run the test with the provided question."""
    # Create workflow
    workflow = create_workflow(enable_semantic_search)
    
    # Prepare input data
    input_data = {
        "original_question": question
    }
    
    # Run the workflow
    result = workflow.run_pipeline(input_data)
    
    # Return result
    return result

def main():
    """Main function to run the test."""
    args = parse_arguments()
    
    logger.info(f"Running semantic search test with question: {args.question}")
    logger.info(f"Semantic search enabled: {not args.no_semantic}")
    
    # Run test with semantic search enabled/disabled
    result = run_test(args.question, enable_semantic_search=not args.no_semantic)
    
    # Save results to file
    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Results saved to {args.output}")
    
    # Print answer
    print("\n" + "="*80)
    print(f"Question: {args.question}")
    print("="*80)
    print(f"Answer: {result.get('answer', 'No answer generated')}")
    print("-"*80)
    print(f"Confidence: {result.get('confidence', 0)}")
    print("="*80)

if __name__ == "__main__":
    main()